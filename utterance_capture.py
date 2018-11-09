################################################################################################################
###   STARTING FROM:
###        https://github.com/markjay4k/Audio-Spectrum-Analyzer-in-Python/blob/master/audio_spectrumQT.py
###   so many thanks to Mark Jay for providing such a great starting point.
###   You should also visit Mark's youtube:
###       https://www.youtube.com/watch?v=AShHJdSIxkY
###       https://www.youtube.com/watch?v=aQKX3mrDFoY
###       https://www.youtube.com/watch?v=RHmTgapLu4s

import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

import struct
import pyaudio
from scipy.fftpack import fft

import sys
import time


class AudioStream(object):
    def __init__(self):
        
        # pyaudio stuff
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100                      # \
        self.RATE = 22050                      #  > Sampling rate
        self.RATE = 11025                      #  |
        #self.RATE = 5512                      # /
        self.CHUNK = 1024 * 2
        
        self.NOISE_FLOOR = 0.002
        self.BIN_COUNT = 100
        self.BIN_WEIGHT = 10.0
        
        self.update_number = 0
        
        self.DELIMITER = ';'
        
        #self.START_TIME
        #self.END_TIME

        ##   plot ranges
        (wf_xmin,wf_xmax) = (0,2 * self.CHUNK)
        (wf_ymin,wf_ymax) = (-130,130)
        (sp_xmin,sp_xmax) = (0,self.RATE / 2)
        (sp_ymin,sp_ymax) = (0,0.02)    # <- The place to change the plotting range for spectral magnitude - helps to better study parts of the spectrum
        
        (sp_xmin_for_vowels, sp_xmax_for_vowels, freq_levels) = (200,4200,self.BIN_COUNT + 1) # spectrum intervals for vowels
        self.bin_width = (sp_xmax_for_vowels - sp_xmin_for_vowels) / self.BIN_COUNT
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.CHUNK,
        )
        
        # pyqtgraph stuff
        pg.setConfigOptions(antialias=True)
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsWindow(title='Spectrum Analyzer')
        self.win.setWindowTitle('Spectrum Analyzer')
        self.win.setGeometry(5, 115, 1810, 870)

        wf_markers = np.linspace(wf_xmin, wf_xmax, 3).astype(int)
        wf_xlabels = []
        for i in np.arange(0,len(wf_markers)):
            wf_xlabels.append((wf_markers[i],str(wf_markers[i])))
        # The preceding 4 lines produce: wf_xlabels = [(0, '0'), (2048, '2048'), (4096, '4096')]
        
        wf_xaxis = pg.AxisItem(orientation='bottom')
        wf_xaxis.setTicks([wf_xlabels])

        wf_ylabels = [(-125, '-125'), (0, '0'), (125, '125')]
        wf_yaxis = pg.AxisItem(orientation='left')
        wf_yaxis.setTicks([wf_ylabels])

        self.waveform = self.win.addPlot(
            title='WAVEFORM', row=1, col=1, axisItems={'bottom': wf_xaxis, 'left': wf_yaxis},
        )
        self.waveform.setYRange(wf_ymin, wf_ymax, padding=0)
        self.waveform.setXRange(wf_xmin, wf_xmax, padding=0.005)
        
        
        sp_markers = np.linspace(sp_xmin, sp_xmax, 41).round(-1).astype(int) # Frequency markings
        sp_xlabels = []
        for i in np.arange(0,len(sp_markers)):
            sp_xlabels.append((sp_markers[i],str(sp_markers[i])))
        #sp_xlabels = [
        #    (np.log10(10), '10'), (np.log10(100), '100'),
        #    (np.log10(1000), '1000'), (np.log10(22050), '22050')
        #]
        #sp_xlabels = [(100, '100'),(1000, '1000'), ... ,(15000, '15000'),(22050, '22050')]
        sp_xaxis = pg.AxisItem(orientation='bottom')
        sp_xaxis.setTicks([sp_xlabels])

        self.spectrum = self.win.addPlot(
            title='SPECTRUM', row=2, col=1, axisItems={'bottom': sp_xaxis},
        )
        self.spectrum.setLogMode(x=False, y=False)
        self.spectrum.setYRange(sp_ymin, sp_ymax, padding=0)
        self.spectrum.setXRange(sp_xmin, sp_xmax, padding=0.005)
        
        inf = pg.InfiniteLine(pos=self.NOISE_FLOOR,
                              movable=False,
                              angle=0,
                              pen=(200, 200, 0),
                              bounds=[sp_xmin,sp_xmax],
                              label='NOISE FLOOR = '+str(self.NOISE_FLOOR),
                              labelOpts={'position':0.9,
                                         'color': (200,200,0),
                                         'movable': True,
                                         'fill': (0, 0, 0, 100)})
        self.spectrum.addItem(inf)
        
        # waveform and spectrum x points
        self.x = np.arange(wf_xmin, wf_xmax, 2)
        self.f = np.linspace(sp_xmin, sp_xmax, int(self.CHUNK / 2))
        
        ############################################################
        ##  Some sites on vowel and consonant formants:
        ##  http://www.phon.ox.ac.uk/jcoleman/consonant_acoustics.htm
        ##  https://www.phon.ucl.ac.uk/home/wells/formants/table-1-uni.htm
        ##  https://www.peterlang.com/view/9783034326179/List_of_figures.xhtml#lof
        ##  https://www.peterlang.com/view/9783034326179/M_Part03.xhtml#rm3fig18c
        ##  https://www.peterlang.com/view/9783034326179/Chapter02.xhtml#rch2fig1
        ##  http://www.antimoon.com/resources/phonchart.htm
        ############################################################
        #   mark out the cut-offs of a linear quantiser
        #   - at some point we could work out a means of adapting these to maximise the recognition of utterances
        sp_cutoffs = np.linspace(sp_xmin_for_vowels, sp_xmax_for_vowels, freq_levels).round(0).astype(int)
        sp_cutoff_pairs = []
        for i in np.arange(0,len(sp_cutoffs) - 1):
            sp_cutoff_pairs.append((sp_cutoffs[i],
                                    sp_cutoffs[i+1],
                                    str(int(sp_cutoffs[i]))+'_to_'+str(int(sp_cutoffs[i+1]))))
        
        self.header = 'Timestamp;'+self.DELIMITER.join(np.array(sp_cutoff_pairs).T[2])
        self.out = np.zeros((2,len(sp_cutoff_pairs) + 1))   # ' + 1' to accommodate the timestamp
        self.t = np.zeros((len(sp_cutoff_pairs),len(self.f)))
        
        for i in np.arange(0,len(sp_cutoff_pairs)):
            lc = sp_cutoff_pairs[i][0]       # passband lower cut-off
            uc = sp_cutoff_pairs[i][1]       # passband upper cut-off
            bin_text = sp_cutoff_pairs[i][2]
            self.t[i] = ((1.0 / (1.0+np.exp(lc-self.f))) - (1.0 / (1.0+np.exp(uc-self.f))))
            text = pg.TextItem(bin_text, anchor=(0.0, 0.5), angle=90, color=(100, 100, 255))
            text.setPos((lc+uc)/2.0,(0.25 * (sp_ymax - sp_ymin)) + sp_ymin) # caters for different y ranges
            self.spectrum.addItem(text)
            
    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'waveform':
                self.traces[name] = self.waveform.plot(pen='c', width=3)
            if name == 'spectrum':
                self.traces[name] = self.spectrum.plot(pen='m', width=3)
            if name[:4] == 'bin_':
                self.traces[name] = self.spectrum.plot(color=(100, 100, 255), style=QtCore.Qt.DashLine)

    def update(self):
        wf_data = self.stream.read(self.CHUNK)
        
        wf_data = np.frombuffer(wf_data,dtype='b')

        wf_data = np.array(wf_data, dtype='b')[::2]
        self.set_plotdata(name='waveform', data_x=self.x, data_y=wf_data,)

        sp_data = fft(np.array(wf_data, dtype='int8'))
        sp_data = np.abs(sp_data[0:int(self.CHUNK / 2)]) * 2 / (128 * self.CHUNK)
        self.set_plotdata(name='spectrum', data_x=self.f, data_y=sp_data)
        
        bin_profile = np.dot(self.t,sp_data)
        for i in np.arange(0,len(bin_profile)):
            bin_data = self.BIN_WEIGHT * bin_profile[i] * self.t[i] / self.bin_width
            self.set_plotdata(name='bin_'+str(i), data_x=self.f, data_y=bin_data)
            
        bin_profile = np.insert(bin_profile,0,time.time())
        self.out = np.append(self.out,[bin_profile],axis=0)
        self.update_number += 1

    def animation(self):
        
        self.output_filename = input("Please enter the filename/path for capturing utterance data: ")
        if self.output_filename[-7:] != '.npydat':
            self.output_filename += '.npydat'

        print("Output filename is: '" + self.output_filename + "'")
        
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        
        self.START_TIME = time.time()
        
        self.start()
        
        self.END_TIME = time.time()
        
        total_updates = self.update_number
        
        run_duration = self.END_TIME - self.START_TIME
        
        print('Run started: '+time.ctime(self.START_TIME))
        print('Run finished: '+time.ctime(self.END_TIME))
        print('Run duration: '+str(run_duration)+' seconds.')
        print('Total updates: '+str(total_updates))
        print('Update rate: '+str(total_updates/run_duration)+' updates per second.')
        
        print("Saving data to '" + self.output_filename + "' ... ", end='')
        np.savetxt(self.output_filename,
                   self.out,
                   delimiter=self.DELIMITER,
                   header=self.header,
                   footer="To read in this file use:'self.out = np.loadtxt('" + self.output_filename + "', delimiter=DELIMITER)'")
        print('done.')


if __name__ == '__main__':

    audio_app = AudioStream()
    audio_app.animation()
    #print(audio_app.t[0].shape,min(audio_app.t[0]),max(audio_app.t[0]))

