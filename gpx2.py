import sys
import datetime as dt
import gpxpy
import numpy as np
from math import sin, cos, pi, sqrt, atan
import matplotlib.pyplot as plt

class GPXFile:
    ''' 
        Obiekt reprezentujący plik GPX 
        Tutaj obliczamy wszytko co jest potrzebne.
    '''

    def __init__(self, filename):
        ''' Wczytaj gpx '''
        lat = []
        lon = []
        el = []
        dates = []
        with open (filename,'r') as gpx_file:
            gpx_dane=gpxpy.parse(gpx_file)
        for track in gpx_dane.tracks:
            for seg in track.segments:
                for point in seg.points:
                    lon.append(point.longitude)
                    lat.append(point.latitude)
                    el.append(point.elevation)
                    if point.time is not None:
                        point.time = point.time.replace(tzinfo=None)
                    dates.append(point.time)
        self.lon = lon
        self.lat = lat
        self.el = el
        self.dates = dates

        # Oblicz xyz 
        self.xyz_points = []
        for lo, la, el in zip(self.lon, self.lat, self.el):
            self.xyz_points.append(GPXFile._to_xyz(lo, la, el))

        # Oblicz długość trasy = suma długości odcinków pomiędzy punktami
        self.segments_len = []
        self.len = 0
        for ptA, ptB in zip(self.xyz_points[:-1], self.xyz_points[1:]):
            l = GPXFile._dist(ptA, ptB) 
            self.len += l
            self.segments_len.append(l)


        # Czas przebycia trasy, jesli są znaczniki na początku i koncu
        try:
            self.total_time = (self.dates[-1] - self.dates[0]).seconds
        except:
            self.total_time = None

        # Sprobujmy obliczyc czasu ma poszczegolnych odcinkach
        self.segments_times = []
        self.all_segments_has_time = True
        for ptA, ptB in zip(self.dates[:-1], self.dates[1:]):
            if ptA is not None and ptB is not None:
                sec = (ptB - ptA).seconds
            else:
                self.all_segments_has_time = False
                sec = None
            self.segments_times.append(sec)

        # Obliczamy MIN i MAX wysokości na trasie
        self.min_z = 99999999
        self.max_z = -99999999
        for z in self.el:
            if z is not None:
                if z > self.max_z:
                    self.max_z = z
                if z < self.min_z:
                    self.min_z = z
        print(self.min_z, self.max_z)

        # Obliczamy przewyzszenia, wzniesienia, spadki
        self.segments_asc = []
        self.segments_desc = []
        self.segments_diff = []
        for ptA, ptB in zip(self.xyz_points[:-1], self.xyz_points[1:]):
            # Dla wszystkich kolejnych odcinków A->B sprwdz czy dane są poprawne
            zA = ptA[2]
            zB = ptB[2]
            if zA is None or zB is None:
                zA = 0
                zB = 0
            # I oblicz roznice wysokosci
            dh = zB - zA
            self.segments_diff.append(dh)
            if dh > 0:
                # Wzniesienie
                self.segments_asc.append(dh)
            if dh < 0:
                # Spadek
                self.segments_desc.append(dh)
        # Oblicz potrzebne sumy
        self.sum_asc = sum(self.segments_asc)
        self.sum_desc = sum(self.segments_desc)
        self.sum_diff = sum(self.segments_diff)

        # Jeśli mamy określony czas trasy, liczymy średnią prędkość!
        if self.total_time == 0:
            print('Uppss  czas równy zero! To zakładamy, że nie mamy.')
            self.total_time = None
        self.avg_vel = (self.len/ self.total_time) if self.total_time is not None else None

        # Najtrudniejszy odcinek (największe nachylenie!!!!)
        # Znajdujemy jakie jest (lat, lon) najtrugniejszego odcinka
        hardest = None
        nach_max = -1
        for lat, lon, dist, h_diff in zip(self.lat[:-1], self.lon[:-1], self.segments_len, self.segments_diff):
            if dist > 0:
                if abs(h_diff) / dist > nach_max:
                    nach_max = abs(h_diff) / dist
                    hardest = lat, lon
        self.hardest = hardest
        self.angle_max = atan(nach_max) / pi * 180
            


    def _dist(A, B):
        ''' Pomocnicza funkcja - dystans pomiędzy punktami'''
        return sqrt(sum([(x - y)**2 for x, y in zip(A[:3], B[:3])]))

    def _to_xyz(lat, lon, el):
        ''' krzywoliniowe do XYZ '''
        valid_el = True
        r_lat = pi * lat / 180
        r_lon = pi * lon / 180

        if el is None:
            el = 0
            valid_el = False
        r = el + 6378137
        x = r * cos(r_lat) * sin(r_lon)
        y = r * sin(r_lat)
        z = r * cos(r_lat) * cos(r_lon)
        return x, y, z, valid_el
    
    def __str__(self):
        ''' Podglad pliku dla testu czy dziala ok '''
        s = 'Długość trasy: %f m\n' % self.len
        if self.total_time is not None:
            s += 'Czas trasy: %f s\n' % self.total_time
            s += 'Predkosc: %f m/s\n' % (self.len/ self.total_time)
        else:
            s += 'Czas trasy: BRAK DANYCH\n'
        return s
    

    def plots(self):
        ''' Rób wykresy! 
            - predkosc od drogi,
            - wysokosc od drogi
        '''
        lens = self.segments_len # odcinki, długości
        times = self.segments_times # czasy odcinków
        vel = []
        l = 0
        len_cum = [] # skumulowana długość
        for x, t in zip(lens, times):
            l += x
            len_cum.append(l)
            if t is None or t == 0:
                vel.append(0)
            else:
                vel.append(x / t)

        fig, ax = plt.subplots(1,1)
        p1, = ax.plot(len_cum, vel, 'r', label='Prędkość')
        ax_ = ax.twinx()
        p2, = ax_.plot(len_cum, self.el[:-1], 'b', label='Wysokość')
        ax.set_xlabel('Dystans [m]')
        ax_.set_ylabel('Wysokość [m]', fontsize=20)
        ax.set_ylabel('Prędkość [m/s]', fontsize=20)
        ax.set_ylim(0, 20)

        # Rysujemy legendę
        ps = [p1, p2]
        plt.legend(ps, [x.get_label() for x in ps], fontsize=15)

        plt.tight_layout()
        plt.title('Prędkość i wysokość vs. odległość')
        plt.savefig('dist-vel-height.png')



if __name__ == '__main__':
    # Test czy wczytywanie jest poprawne
    gpxfile = GPXFile(sys.argv[1])
    print(gpxfile)
