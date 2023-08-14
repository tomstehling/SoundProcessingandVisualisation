import sys
import queue
import sounddevice as sd
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QSpinBox, QLabel
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

queue = queue.Queue()
blocksize=441

global threshold_mid, threshold_high, t_integrate,t_lenght, n_bars, f_min, f_max


#############################################################################################
########################################     GUI     ########################################
#############################################################################################


############################
###     MAIN WINDOW      ###
############################


"""
Klasse die das Hauptfenster repräsentiert und alle Elemente die sichtbar sind beinhaltet
"""
class Audio_App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title="AudioApp"
        self.setStyleSheet("background-color:#FFC023;")
        self.setFixedSize(900, 600)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.plot_levelmeter = Levelmeter(self,width=3, height=1)
        self.plot_waveform = Waveform(self,width=4, height=3)
        self.plot_spectrum = Spectrum(self, width=4, height=3)
        self.plot_levelmeter.move(0,0)
        self.plot_waveform.move(25,200)
        self.plot_spectrum.move(475,200)

        self.setup_spinbox()
        self.get_spinbox_value()
        self.show()

    """
        Funktion, die die Spinboxen und die dazugehörigen Labels erstellt.
        """

    def setup_spinbox(self):

        # T_Lenght Label + Spinbox
        t_lenght_label = QLabel(self)
        t_lenght_label.setText('T len in ms')
        t_lenght_label.move(180, 510)
        self.t_lenght_spinbox = QSpinBox(self)
        self.t_lenght_spinbox.move(180, 540)
        self.t_lenght_spinbox.setMinimum(1)
        self.t_lenght_spinbox.setMaximum(10)
        self.t_lenght_spinbox.valueChanged.connect(self.get_spinbox_value)



        # N_Bars Label + Spinbox
        n_bars_label = QLabel(self)
        n_bars_label.setText('half bars x times')
        n_bars_label.move(475, 510)
        self.n_bars_spinbox = QSpinBox(self)
        self.n_bars_spinbox.setSuffix("x")
        self.n_bars_spinbox.move(475, 540)
        self.n_bars_spinbox.setMinimum(0)
        self.n_bars_spinbox.setMaximum(3)
        self.n_bars_spinbox.setValue(0)
        self.n_bars_spinbox.setSingleStep(1)
        self.n_bars_spinbox.valueChanged.connect(self.get_spinbox_value)


        # F_Min Label + Spinbox
        f_min_label = QLabel(self)
        f_min_label.setText('Fmin')
        f_min_label.move(630, 510)
        self.f_min_spinbox = QSpinBox(self)
        self.f_min_spinbox.move(630, 540)
        self.f_min_spinbox.setMinimum(1)
        self.f_min_spinbox.setMaximum(5000)
        self.f_min_spinbox.setValue(300)
        self.f_min_spinbox.setSingleStep(100)
        self.f_min_spinbox.valueChanged.connect(self.get_spinbox_value)

        # F_Max Label + Spinbox
        f_max_label = QLabel(self)
        f_max_label.setText('Fmax')
        f_max_label.move(780,510)
        self.f_max_spinbox = QSpinBox(self)
        self.f_max_spinbox.move(780, 540)
        self.f_max_spinbox.setMinimum(5000)
        self.f_max_spinbox.setMaximum(22000)
        self.f_max_spinbox.setValue(5000)
        self.f_max_spinbox.setSingleStep(100)
        self.f_max_spinbox.valueChanged.connect(self.get_spinbox_value)


        # Threshold Mid Label + Spinbox
        threshold_mid_label = QLabel(self)
        threshold_mid_label.setText('Threshold Mid')
        threshold_mid_label.move(500, 0)

        self.threshold_mid_spinbox = QSpinBox(self)
        self.threshold_mid_spinbox.setSuffix("%")
        self.threshold_mid_spinbox.setMinimum(-100)
        self.threshold_mid_spinbox.setMaximum(100)
        self.threshold_mid_spinbox.setSingleStep(20)
        self.threshold_mid_spinbox.move(500, 50)
        self.threshold_mid_spinbox.valueChanged.connect(self.get_spinbox_value)

        # Threshold High Label + Spinbox
        threshold_high_label = QLabel(self)
        threshold_high_label.setText('Threshold High')
        threshold_high_label.move(600, 0)

        self.threshold_high_spinbox = QSpinBox(self)
        self.threshold_high_spinbox.setMinimum(-100)
        self.threshold_high_spinbox.setMaximum(100)
        self.threshold_high_spinbox.setSingleStep(20)
        self.threshold_high_spinbox.move(600,50)
        self.threshold_high_spinbox.setSuffix("%")
        self.threshold_high_spinbox.valueChanged.connect(self.get_spinbox_value)

        # T_Integrate Label + Spinbox
        t_integrate_label = QLabel(self)
        t_integrate_label.setText('T Integrate in ms')
        t_integrate_label.move(700, 0)

        self.t_integrate_spinbox = QSpinBox(self)
        self.t_integrate_spinbox.move(700, 50)
        self.t_integrate_spinbox.setMinimum(1)
        self.t_integrate_spinbox.setMaximum(10)
        self.t_integrate_spinbox.setValue(10)
        self.t_integrate_spinbox.valueChanged.connect(self.get_spinbox_value)

    """
        Funktion, die aufgerufen wird, wenn der Wert in einer Spinbox geändert wurde. Sie setzt die Globalen Variablen, gleich den Werten der Spinboxen.
       
        """
    def get_spinbox_value(self):
            global threshold_mid, threshold_high, t_integrate, t_lenght, n_bars, f_min, f_max

            #Levelmeter
            threshold_mid = self.threshold_mid_spinbox.value()
            threshold_high = self.threshold_high_spinbox.value()
            t_integrate = self.t_integrate_spinbox.value()

            #Waveform
            t_lenght = self.t_lenght_spinbox.value()

            #Spectrum

            n_bars = self.n_bars_spinbox.value()
            f_min = self.f_min_spinbox.value()
            f_max = self.f_max_spinbox.value()
            return




#####################
###     PLOTS     ###
#####################

"""
    Klasse, die die Pegelanzeige repräsentiert
    """
class Levelmeter(FigureCanvas):
    def __init__(self,parent=None,width=5, height=4,dpi=100):
        fig=Figure(figsize=(width,height),dpi=dpi)
        FigureCanvas.__init__(self,fig)
        self.setParent(parent)



        self.levelmeter_plot = fig.add_subplot(111)


        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.plot_levelmeter)
        self.timer.start()

    """
        Funktion, die den Pegelwert grafisch darstellt
       
        """
    def plot_levelmeter(self):

        level=x.calc_level()
        if level=='low level':
            color="w"
        elif level=='medium level':
            color="g"
        elif level=="high level":
            color="r"
        self.levelmeter_plot.cla()
        self.levelmeter_plot.pie([1], colors=color)
        self.draw()

"""
    Klasse, die die Audiodaten als Oszilloskop darstellt
    """

class Waveform(FigureCanvas):
    def __init__(self, parent=None,width=5, height=4,dpi=100,):
        fig=Figure(figsize=(width,height),dpi=dpi)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

###################

        self.wave_plot=fig.add_subplot(111)
        self.wave_plot.set_facecolor("xkcd:salmon")

        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.plot_waveform)
        self.timer.start()




    def plot_waveform(self):
        data = x.get_audio_data()
        self.wave_plot.cla()
        self.wave_plot.plot(data, "b")
        self.wave_plot.set_ylim([-20e3, 20e3])
        self.wave_plot.ticklabel_format(axis="y", style="sci", scilimits=(0,0))

        global t_lenght
        #441 Samples represent 10ms
        self.wave_plot.set_xlim(0, (t_lenght*44.1))
        self.wave_plot.set_title('Waveform')
        self.wave_plot.tick_params(axis="x", which="both",bottom=False, top=False, labelbottom=False)
        self.draw()


"""KLasse die das Spektrum repräsentiert"""
class Spectrum(FigureCanvas):
    def __init__(self,parent=None,width=5, height=4,dpi=100):
        fig=Figure(figsize=(width,height),dpi=dpi)
        FigureCanvas.__init__(self,fig)
        self.setParent(parent)



        self.spectrum_plot = fig.add_subplot(111)
        self.spectrum_plot.set_facecolor('xkcd:yellow')

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.plot_spectrum)
        self.timer.start()

    def set_plot_params(self):
        global f_min, f_max, n_bars
        step=2**n_bars

        data = x.fft()

        self.data_to_plot = []

        for i in np.arange(0, len(data), step):
            self.data_to_plot.append(data[i])




        self.width = 50 * step

        self.x_axis=[x for x in np.arange(0, 22000, 100 * step)]
        self.x_min =f_min
        self.x_max =f_max

        self.y_min =0
        self.y_max =0.03


    def plot_spectrum(self):
        self.set_plot_params()
        self.spectrum_plot.cla()
        self.spectrum_plot.bar(self.x_axis, self.data_to_plot, width=self.width)
        self.spectrum_plot.set_ylim([self.y_min, self.y_max])
        self.spectrum_plot.set_xlim([self.x_min, self.x_max])

        self.spectrum_plot.set_xscale('log')
        self.spectrum_plot.set_title('Spectrum')

        self.draw()




#############################################################################################
########################################     LOGIC     ######################################
#############################################################################################

        """
        Liest das Mikrofon aus
        und gibt die Daten in eine Warteschlange.
        Parameter: indata, frames, time, status
        Return:None
        """
def callback(indata, frames, time, status):
    queue.put(indata)
rec = sd.InputStream(samplerate=44100, blocksize = 441,channels=1, callback = callback,dtype = 'int16')
rec.start()



class Logic():

    def __init__(self,blocksize):
        self.blocksize=blocksize

        """
        Funktion, die die Audiodaten blockweise aus der Warteschlange entnimmt.
        Return: Array mit Audiodaten; 441 Einträge
        """
    def get_audio_data(self):
        self.audio_data = queue.get()
        return self.audio_data


    #################
    ################# PEGELANZEIGE

        """
        Funktion, die einen Array erstellt und diesen mit Audiodaten füllt, die dann später integriert werden sollen.
        Return: Array mit Audiodaten, Länge (44-440) entspricht einer bis 10 Millisekunden
        """
    def samples_to_be_integrated(self):
        global t_integrate
        list = self.get_audio_data()
        samples = []
        for i in range(t_integrate*44):
            samples.append(abs(list[i][0]))
        return samples

        """
        Funktion, die den RMS aus einem Array bestimmt
        Return: float
        """
    def rms(self):
        array=self.samples_to_be_integrated()
        sum = 0
        for i in array:
            sum += i ** 2
        msum = sum / len(array)
        rms = np.sqrt(msum)
        return rms

        """
        Funktion, die aus dem RMS Wert den Pegel bestimmt.
        Globale Variablen: Schwellwert Mittel und Schwellwert Laut
        Return: String
        """
    def calc_level(self):
        global threshold_mid, threshold_high

        threshold_mid_value=550
        threshold_high_value=6000
        threshold_mid_abs=threshold_mid_value+(threshold_mid*5)
        threshold_high_abs=threshold_high_value+(threshold_high*40)
        energy = self.rms()
        if energy < threshold_mid_abs:
            return "low level"
        elif threshold_mid < energy < threshold_high_abs:
            return "medium level"
        else: #energy > threshold_high:
            return"high level"

    #############################
    ############        FOURIER

        """
        Funktion, die die Audiodaten für die Frequenzanalyse bekommt
        Return: Array mit Audiodaten
        """
    def get_samples_spectrum(self):
        list = self.get_audio_data()
        samples = []
        for i in range(len(list)):
            samples.append(list[i][0])
        return samples

        """
        Funktion, die eine Fourier Transformation durchführt und die transformierten Daten zurückgibt
        Return: Array mit 220 Einträgen
        """

    def fft(self):
        fft=np.abs(np.fft.fft(self.get_samples_spectrum()))
        fft2=[]
        for i in range(  int(((len(fft))-1)/2) )  :
            fft2.append(fft[i]*2/((2**16)*self.blocksize))
        return fft2






if __name__=="__main__":
    x=Logic(blocksize)
    app = QApplication(sys.argv)
    ex = Audio_App()
    sys.exit(app.exec_())
