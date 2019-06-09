from kivy.app import App  
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup # Okno, wybor pliku
from kivy.uix.textinput import TextInput

from kivy.uix.boxlayout import BoxLayout  
from kivy.properties import ObjectProperty  
from kivy.garden.mapview import MapMarker, MarkerMapLayer, MapView, MapSource

import matplotlib.pyplot as plt
import os

# Moja klasa dla plików GPX
from gpx2 import GPXFile


class Menu(FloatLayout):
    ''' Wczytywanie pliku '''
    action_load = ObjectProperty(None)
    action_cancel = ObjectProperty(None)


class CoreApp(BoxLayout):

    #===== Obsluga wczytywania pliku =========================================
    def load_button_pressed_(self):
        dialog = Menu(action_load=self.get_file, action_cancel=self.close_dialog)
        self.get_file_dialog = Popup(title="Wybierz plik", content=dialog)
        self.get_file_dialog.open()


    def get_file(self, path, fname):
        ''' wczytaj wybrany gpx'''
        path = os.path.join(path, fname[0])
        self.loaded_gpx = GPXFile(path)
        self.gpx_file_.text = str(path)
        self.close_dialog()
        print(self.loaded_gpx)
        self.update_controls()


    def close_dialog(self):
        ''' Zamkinj okienko '''
        self.get_file_dialog.dismiss()
    #===== KONIEC obslugi wczytywania pliku ==================================


    #===== Aktualizuj pola tektowe   =========================================
    def update_controls(self):
        ''' Aktualizuj wskazania w okienku aplikacji '''
        # Wypisz drogę!
        self.label_total_len_.text = "%.3fm" % self.loaded_gpx.len
        # Wypisz czas
        T = self.loaded_gpx.total_time
        if T is None:
            self.label_total_time_.text = 'BRAK DANYCH!'
        else:
            h = int(T) / 3600
            m = int(T / 60) % 60
            s = int(T % 60)
            self.label_total_time_.text = '%dh %dm %ds' % (h, m, s)

        # Wypisz prędkość!
        avg_vel = self.loaded_gpx.avg_vel
        if avg_vel is None:
            self.label_total_avg_vel_.text = 'BRAK DANYCH!'
        else:
            self.label_total_avg_vel_.text = '%.3fm/s' % avg_vel

        # Aktualizuj pozostałe kontrolki
        self.label_total_sum_diff_.text = '%.3fm' % self.loaded_gpx.sum_diff
        self.label_total_sum_asc_.text = '%.3fm' % self.loaded_gpx.sum_asc
        self.label_total_sum_desc_.text = '%.3fm' % self.loaded_gpx.sum_desc
        self.label_total_z_min_.text = '%.3fm' % self.loaded_gpx.min_z
        self.label_total_z_max_.text = '%.3fm' % self.loaded_gpx.max_z


        h_lat, h_lon = self.loaded_gpx.hardest
        self.label_hard_pos_.text = "%.4f %.4f" % (h_lat, h_lon)
        self.label_hard_angle_.text = "%.2f'" % self.loaded_gpx.angle_max

        # Rysuj max 50 markerów na mapie i połozenie najtrudniejszego miejsca
        self.draw_markers(self.loaded_gpx.lat, self.loaded_gpx.lon, h_lat, h_lon)
        self.loaded_gpx.plots()


    def draw_markers(self, lats, lons, h_lat, h_lon):
        ''' Rysuj markery! I najtrudniejsze miejsce'''
        # Ale najpierw skasujmy stare markery
        self.remove_markers()
        self.data_layer = MarkerMapLayer()
        self.map_.add_layer(self.data_layer)
        # Nie chcemy za dużo punktów narysować
        if len(lats) > 50:
            print('ZA DUŻO PUNKTÓW GPS!!!!')
            co_ile = int(len(lats) / 50)
            print('Wybieramy co %d punkt aby wyświetlić  50/51 punktów')
            lats = lats[::co_ile]
            lons = lons[::co_ile]

        for lat, lon in zip(lats, lons):
            marker = MapMarker(lat=lat, lon=lon)
            self.map_.add_marker(marker, layer=self.data_layer)
        n = len(lats)
        # Ładnie centrujemy mapkę!
        self.map_.center_on(sum(lats) / n, sum(lons) / n)
        # Rysuj położenie najtrudniejszego odcinka
        marker = MapMarker(lat=h_lat, lon=h_lon, source='cluster.png')
        self.map_.add_marker(marker, layer=self.data_layer)



    def remove_markers(self):
        try:
            self.map_.remove_layer(self.data_layer)
            self.data_layer = None
        except:
            pass


    def clear_button_pressed_(self):
        print("CZYŚCIMY DANE!")
        self.remove_markers()
        self.loaded_gpx = None
        self.label_total_sum_diff_.text = '--'
        self.label_total_sum_asc_.text = '--'
        self.label_total_sum_desc_.text = '--'
        self.label_total_z_min_.text = '--'
        self.label_total_z_max_.text = '--'
        self.label_total_avg_vel_.text = '--'
        self.label_total_time_.text = '--'
        self.label_total_len_.text = "--"
        self.label_hard_pos_.text = "--"
        self.label_hard_angle_.text = "--"
        self.gpx_file_.text = '-----'


class MyMapsApp(App):
    ''' Main application class.  '''

    def build(self):
        return CoreApp()
    

if __name__ == '__main__':
    # Run application
    MyMapsApp().run()
