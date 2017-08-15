#!/usr/bin/python
# -*- coding: cp1252 -*-
# -*- coding: <<encoding>> -*-

import wx, wx.xrc, wx.html
import sys
import serial
import serial.tools.list_ports
import time
import threading

#For Plotsection
import numpy
import matplotlib
import matplotlib.patches as patches
matplotlib.use('WXAgg')

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure
import pylab
import icon


#--------------------------------------------------------------------------------------
        
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


###########################################################################
## Class PlotPanel                                                        #
###########################################################################

class PrepWindow(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.axes_point = self.figure.add_subplot(111)
        
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.bSizer_main = wx.BoxSizer( wx.VERTICAL )
        self.bSizer_main.Add(self.canvas, 100, wx.LEFT | wx.TOP | wx.GROW)
        self.Fit()

        self.m_panel_btw = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_panel_btw.SetBackgroundColour( wx.Colour( 240, 240, 240 ) )
        self.bSizer_main.Add( self.m_panel_btw, 2, wx.EXPAND, 5 )

        self.bSizer_sub = wx.BoxSizer( wx.HORIZONTAL )
        
        self.sbSizer_x = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Pulslänge" ), wx.VERTICAL )
        self.sbSizer_x_sub= wx.BoxSizer( wx.HORIZONTAL )

        #Slider  Pulslänge------------------------------------------
        self.m_text_first = wx.StaticText( self.sbSizer_x.GetStaticBox(), wx.ID_ANY, u"1 ms", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_text_first.Wrap( -1 )
        self.sbSizer_x_sub.Add( self.m_text_first, 0, wx.ALL, 5 )
        
        self.m_slider_x = wx.Slider( self.sbSizer_x.GetStaticBox(), wx.ID_ANY, 10, 1, 500, wx.DefaultPosition, wx.Size( 200,-1 ), wx.SL_HORIZONTAL|wx.SIMPLE_BORDER )
        self.m_slider_x.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_MENU ) )
        self.m_slider_x.Bind(wx.EVT_SLIDER, self.OnSliderScroll_x)
    
        self.sbSizer_x_sub.Add( self.m_slider_x, 1, wx.ALL, 5 )

        self.m_text_last = wx.StaticText( self.sbSizer_x.GetStaticBox(), wx.ID_ANY, u"500 ms", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_text_first.Wrap( -1 )
        self.sbSizer_x_sub.Add( self.m_text_last, 0, wx.ALL, 5 )

        self.sbSizer_x.Add( self.sbSizer_x_sub, 0, wx.ALL, 5 )

        self.m_text_diff_slider_x = wx.StaticText( self.sbSizer_x.GetStaticBox(), wx.ID_ANY, u"10 ms", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_text_diff_slider_x.Wrap( -1 )
        self.sbSizer_x.Add( self.m_text_diff_slider_x, 1, wx.ALIGN_CENTER, 2)

        self.sbSizer_y = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Volumen/Puls" ), wx.VERTICAL )
        self.sbSizer_y_sub= wx.BoxSizer( wx.HORIZONTAL )

        #Slider Volumen------------------------------------------
        self.m_text_first_y = wx.StaticText( self.sbSizer_y.GetStaticBox(), wx.ID_ANY, u"6 µl", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_text_first.Wrap( -1 )
        self.sbSizer_y_sub.Add( self.m_text_first_y, 0, wx.ALL, 5 )
        
        self.m_slider_y = wx.Slider( self.sbSizer_y.GetStaticBox(), wx.ID_ANY, 13.2, 6, 500, wx.DefaultPosition, wx.Size( 200,-1 ),wx.SL_HORIZONTAL|wx.SIMPLE_BORDER )
        self.m_slider_y.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_MENU ) )
        self.m_slider_y.Bind(wx.EVT_SLIDER, self.OnSliderScroll_y)
        
        self.sbSizer_y_sub.Add( self.m_slider_y, 1, wx.ALL, 5 )

        self.m_text_last_y = wx.StaticText( self.sbSizer_y.GetStaticBox(), wx.ID_ANY, u"500 µl", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_text_first.Wrap( -1 )
        self.sbSizer_y_sub.Add( self.m_text_last_y, 0, wx.ALL, 5 )

        self.sbSizer_y.Add( self.sbSizer_y_sub, 0, wx.ALL, 5 )

        self.m_text_diff_slider_y = wx.StaticText( self.sbSizer_y.GetStaticBox(), wx.ID_ANY, u"13.2 µl", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_text_diff_slider_y.Wrap( -1 )
        self.sbSizer_y.Add( self.m_text_diff_slider_y, 1, wx.ALIGN_CENTER, 2)
        
        self.m_sdbSizer_dialog = wx.StdDialogButtonSizer()
        self.m_sdbSizerOK = wx.Button( self, wx.ID_OK, u"Übernehmen")
        self.m_sdbSizer_dialog.AddButton( self.m_sdbSizerOK )
        self.m_sdbSizer_Cancel = wx.Button( self, wx.ID_CANCEL, u"Schließen" )
        self.m_sdbSizer_dialog.AddButton( self.m_sdbSizer_Cancel )
        self.m_sdbSizer_dialog.Realize();

        self.m_panel_left = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_panel_left.SetBackgroundColour( wx.Colour( 240, 240, 240 ) )
        self.m_panel_left.SetMaxSize( wx.Size( 1,-1 ) )

        self.m_panel_right = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_panel_right.SetBackgroundColour( wx.Colour( 240, 240, 240 ) )
        self.m_panel_right.SetMaxSize( wx.Size( 1,-1 ) )

        self.m_panel_right_right = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_panel_right_right.SetBackgroundColour( wx.Colour( 240, 240, 240 ) )
        self.m_panel_right_right.SetMaxSize( wx.Size( 1,-1 ) )
        
        self.m_panel_middle = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_panel_middle.SetBackgroundColour( wx.Colour( 240, 240, 240 ) )
        self.m_panel_middle.SetMaxSize( wx.Size( 10,-1 ) )

        self.bSizer_sub.Add( self.m_panel_left,1, wx.EXPAND |wx.ALL, 5 )
        self.bSizer_sub.Add( self.sbSizer_x, 1,wx.EXPAND, 5 )
        self.bSizer_sub.Add( self.m_panel_middle, 1,wx.EXPAND, 5 )
        self.bSizer_sub.Add( self.sbSizer_y, 1,wx.EXPAND, 5 )
        self.bSizer_sub.Add( self.m_panel_right,1, wx.EXPAND |wx.ALL, 5 )
        self.bSizer_sub.Add( self.m_sdbSizer_dialog,1, wx.EXPAND |wx.ALL, 5 )
        self.bSizer_sub.Add( self.m_panel_right_right,1, wx.EXPAND |wx.ALL, 5 )
        
        self.bSizer_main.Add( self.bSizer_sub, 1, wx.EXPAND, 5 )
        self.m_panel_down = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        self.m_panel_down.SetBackgroundColour( wx.Colour( 240, 240, 240 ) )
        self.bSizer_main.Add( self.m_panel_down, 2, wx.EXPAND, 5 )
        
        self.SetSizer( self.bSizer_main )
        self.Layout()
        
        self.Centre( wx.BOTH )

    def draw(self,scale_xy):
        self.axes.set_facecolor('#c8d3d4')
        self.axes.set_title(u'Kammer: Vakuum     Schlauchende: Atmosphäre', size=12)
        self.axes.set_xlabel(u'Pulslänge (ms)')
        self.axes.set_ylabel(u'Volumen / Puls (µl)')
        self.axes.set_xlim(0,scale_xy)
        self.axes.set_ylim(0,scale_xy)
        self.axes.grid(linestyle="--", linewidth=0.5, color='.25', zorder=10)

        pylab.setp(self.axes.get_xticklabels(), fontsize=10)
        pylab.setp(self.axes.get_yticklabels(), fontsize=10)
        
        t = numpy.arange(0, 600, 5.0)
        s = 4.2667+0.89261*t
 
        y1=6.2667+0.89261*t
        y2=2.2667+0.89261*t
        
        self.axes.plot(
            t, y1, t, y2, color='b',
            linewidth=0.5, alpha = 0.5
            )

        self.axes.fill_between(t, y1, y2,color='blue', alpha=.1)        

        self.axes.plot(
            t, s,
            linewidth=1, alpha = 1
            )

    def draw_point(self,p_xa):
        p_x = p_xa
        p_y = 4.2667+0.89261*p_xa
        #self.axes_point.axhline(y= p_y, xmin = 0.0, xmax = p_x, linestyle=":" ,linewidth=0.5, color = 'b')
        #self.axes_point.axvline(x= p_x, ymin = 0.0, ymax = p_y, linestyle=":" ,linewidth=0.5, color = 'b')
        self.axes_point.plot(
            p_x,
            p_y,
            'ro',
        )
        self.axes_point.add_patch(
            patches.Rectangle(
            (0, 0),         # (x,y)
            p_x,            # width
            p_y,            # height
            fill=False,     # remove background
            edgecolor="b",
            linestyle=":" ,
            linewidth=1
            )
        )

    def OnSliderScroll_x(self, e): 
        obj_x = e.GetEventObject() 
        val_x = obj_x.GetValue()
        self.m_text_diff_slider_x.SetLabel(str(val_x)+" ms")
        self.m_slider_y.SetValue(round(4.2667+0.89261*val_x ,1))
        self.m_text_diff_slider_y.SetLabel(str(round(4.2667+0.89261*val_x ,1))+" µl")

        if 200 > self.m_slider_x.GetValue() >= 100:
            self.axes_point.cla()
            self.draw(220)
            self.draw_point(val_x)
            self.figure.canvas.draw()
            
        elif 300 > self.m_slider_x.GetValue() >= 200:
            self.axes_point.cla()
            self.draw(320)
            self.draw_point(val_x)
            self.figure.canvas.draw()
            
        elif 400 > self.m_slider_x.GetValue() >= 300:
            self.axes_point.cla()
            self.draw(420)
            self.draw_point(val_x)
            self.figure.canvas.draw()

        elif 500 >= self.m_slider_x.GetValue() >= 400:
            self.axes_point.cla()
            self.draw(520)
            self.draw_point(val_x)
            self.figure.canvas.draw()              

        elif self.m_slider_x.GetValue() < 100:
            self.axes_point.cla()
            self.draw(110)
            self.draw_point(val_x)
            self.figure.canvas.draw()

    def global_ret(self):
        self.puls = self.m_slider_x.GetValue()
        return self.puls

    def OnSliderScroll_y(self, e): 
        obj_y = e.GetEventObject() 
        val_y = obj_y.GetValue()

        calval_x = ((val_y-4.2667)/0.89261) 
        self.m_text_diff_slider_y.SetLabel(str(val_y)+" µl")
        self.m_slider_x.SetValue(int(calval_x))
        self.m_text_diff_slider_x.SetLabel(str(int(calval_x))+" ms")

        if 200 > self.m_slider_y.GetValue() >= 100:
            self.axes_point.cla()
            self.draw(260)
            self.draw_point(calval_x)
            self.figure.canvas.draw()
            
        elif 300 > self.m_slider_y.GetValue() >= 200:
            self.axes_point.cla()
            self.draw(360)
            self.draw_point(calval_x)
            self.figure.canvas.draw()
            
        elif 400 > self.m_slider_y.GetValue() >= 300:
            self.axes_point.cla()
            self.draw(460)
            self.draw_point(calval_x)
            self.figure.canvas.draw()

        elif 500 >= self.m_slider_y.GetValue() >= 400:
            self.axes_point.cla()
            self.draw(560)
            self.draw_point(calval_x)
            self.figure.canvas.draw()              

        elif self.m_slider_y.GetValue() < 100:
            self.axes_point.cla()
            self.draw(110)
            self.draw_point(calval_x)
            self.figure.canvas.draw()

    def __del__( self ):
        pass


###########################################################################
## Class MainFrame                                                        #
###########################################################################

class MainFrame ( wx.Frame ):
        def __init__( self, title ):
                wx.Frame.__init__ ( self, None, title = title, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 440,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

                self.SetIcon(icon.iconset.GetIcon())
                self.SetSizeHintsSz( wx.Size( 430,600 ), wx.Size( 430,600 ) )
                self.SetBackgroundColour( wx.Colour( 240, 240, 240 ) )
                self.Bind(wx.EVT_CLOSE, self.OnClose)

                #Menu and statusbar section
                self.m_statusBar = self.CreateStatusBar( 1, wx.ST_SIZEGRIP, wx.ID_ANY )
                self.m_statusBar.SetFieldsCount(3) 
                self.progress_bar = wx.Gauge(self.m_statusBar, -1, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH) 
                rect = self.m_statusBar.GetFieldRect(2) 
                self.progress_bar.SetPosition((rect.x+2, rect.y+2)) 
                self.progress_bar.SetSize((rect.width-4, rect.height-4)) 

                self.progress_bar.Hide()
                
                self.m_menubar = wx.MenuBar( 0 )
                self.m_menu1 = wx.Menu()
                m_exit = wx.MenuItem( self.m_menu1, wx.ID_EXIT, u"Beenden","\tFenster schließen", wx.ITEM_NORMAL )
                m_gerade = wx.MenuItem( self.m_menu1, wx.ID_ANY, u"Volumen","\tPräparationgerade", wx.ITEM_NORMAL )
                self.Bind(wx.EVT_MENU, self.prep_open, m_gerade)
                self.Bind(wx.EVT_MENU, self.OnClose, m_exit)
                self.m_menu1.AppendItem( m_gerade ) 
                self.m_menu1.AppendItem( m_exit )
                self.m_menubar.Append( self.m_menu1, u"Datei" ) 
                
                self.m_menu2 = wx.Menu()
                m_about = wx.MenuItem( self.m_menu2, wx.ID_ABOUT, u"Über", "\tInfos", wx.ITEM_NORMAL )
                self.Bind(wx.EVT_MENU, self.OnAboutBox, m_about)
                self.m_menu2.AppendItem( m_about )
                
                self.m_menubar.Append( self.m_menu2, u"Hilfe" ) 
                
                self.SetMenuBar( self.m_menubar )
                
                bSizer_main = wx.BoxSizer( wx.VERTICAL )
                
                self.m_bitmap_head = wx.StaticBitmap( self, wx.ID_ANY, wx.Bitmap( u"Duty.bmp", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.Size( -1,50), 0 )
                bSizer_main.Add( self.m_bitmap_head, 0, wx.ALL|wx.EXPAND, 5 )

                self.m_staticline03 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
                bSizer_main.Add( self.m_staticline03, 0, wx.EXPAND |wx.ALL, 5 )                

                             

                #Parametersection -----------------------------------------------
                sbSizer_param = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Parameter" ), wx.VERTICAL )
                
                bSizer2 = wx.BoxSizer( wx.HORIZONTAL )
                
                self.m_static_on = wx.StaticText( sbSizer_param.GetStaticBox(), wx.ID_ANY, u"T on (ms)     ", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.m_static_on.Wrap( -1 )
                bSizer2.Add( self.m_static_on, 0, wx.ALL, 5 )
                #self.m_static_on.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )

                        #onTime TextCtrl ----------------------------------------
                self.m_text_on = wx.TextCtrl( sbSizer_param.GetStaticBox(),wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
                self.m_text_on.SetMinSize( wx.Size( 100,-1 ) )
                #self.m_text_on.SetFocus()
                
                bSizer2.Add( self.m_text_on, 0, wx.ALL|wx.EXPAND, 5 )
                #self.m_text_on.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )

                self.m_panel11 = wx.Panel( sbSizer_param.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( 10,-1 ), wx.TAB_TRAVERSAL )
                bSizer2.Add( self.m_panel11, 0, wx.EXPAND |wx.ALL, 5 )
                self.m_panel11.Enable( False )
                
                self.m_static_off = wx.StaticText( sbSizer_param.GetStaticBox(), wx.ID_ANY, u"      T off (ms)", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.m_static_off.Wrap( -1 )
                bSizer2.Add( self.m_static_off, 0, wx.ALL, 5 )
                
                        #offTime TextCtrl ---------------------------------------
                self.m_text_off = wx.TextCtrl( sbSizer_param.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
                self.m_text_off.SetMinSize( wx.Size( 100,-1 ) )
                
                bSizer2.Add( self.m_text_off, 0, wx.ALL|wx.EXPAND, 5 )
                
                sbSizer_param.Add( bSizer2, 1, wx.EXPAND, 5 )
                
                bSizer3 = wx.BoxSizer( wx.HORIZONTAL )
                
                self.m_static_cycle = wx.StaticText( sbSizer_param.GetStaticBox(), wx.ID_ANY, u"Anzahl Pulse", wx.DefaultPosition, wx.DefaultSize, 0 )
                self.m_static_cycle.Wrap( -1 )
                bSizer3.Add( self.m_static_cycle, 0, wx.ALL|wx.EXPAND, 5 )
                #self.m_static_cycle.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )

                        #pulse TextCtrl ------------------------------------------
                self.m_text_pulse = wx.TextCtrl( sbSizer_param.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
                self.m_text_pulse.SetMinSize( wx.Size( 100,-1 ) )
                #self.m_text_pulse.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )
                
                bSizer3.Add( self.m_text_pulse, 0, wx.ALL|wx.EXPAND, 5 )

                self.m_panel10 = wx.Panel( sbSizer_param.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( 20,-1 ), wx.TAB_TRAVERSAL )
                bSizer3.Add( self.m_panel10, 0, wx.EXPAND |wx.ALL, 5 )
                self.m_panel10.Enable( False )

                        #Speichern Button ----------------------------------------              
                self.m_button_speichern = wx.Button( sbSizer_param.GetStaticBox(), wx.ID_ANY, u"Speichern", wx.DefaultPosition, wx.Size( 170,20 ), 0 )
                self.m_button_speichern.SetToolTipString( u"Speichert die Parameter im EEProm des Interfaces" )
                self.m_button_speichern.Bind(wx.EVT_BUTTON, self.onEnter_ont)
                bSizer3.Add( self.m_button_speichern, 0, wx.ALL|wx.EXPAND, 5 )
                #self.m_button_speichern.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )
                
                
                sbSizer_param.Add( bSizer3, 1, wx.EXPAND, 5 )
                
                bSizer5 = wx.BoxSizer( wx.VERTICAL )
                
                self.m_panel6 = wx.Panel( sbSizer_param.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
                bSizer5.Add( self.m_panel6, 0, wx.EXPAND |wx.ALL, 5 )
                
                
                sbSizer_param.Add( bSizer5, 0, wx.EXPAND, 5 )
                
                bSizer_main.Add( sbSizer_param, 0, wx.ALL|wx.EXPAND, 5 )

                self.m_staticline3 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
                bSizer_main.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )               

                bSizer_mod_vol = wx.BoxSizer( wx.HORIZONTAL )



                #Modussection -------------------------------------------------------
                sbSizer_modus = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Modus" ), wx.VERTICAL )
                
                bSizer6 = wx.BoxSizer( wx.HORIZONTAL )
                
                    #Pulse ----------------------------------------------------------
                self.m_radio_pulse = wx.RadioButton( sbSizer_modus.GetStaticBox(), wx.ID_ANY, u"Pulse", wx.DefaultPosition, wx.DefaultSize, 0 )
                bSizer6.Add( self.m_radio_pulse, 0, wx.ALL|wx.EXPAND, 5 ) 
                #self.m_radio_pulse.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )
                self.m_radio_pulse.Bind(wx.EVT_LEFT_DOWN, self.radio_pulse)
                
                self.m_staticline2 = wx.StaticLine( sbSizer_modus.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL|wx.LI_VERTICAL )
                bSizer6.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )
  

                    #Reinigen -------------------------------------------------------
                self.m_radio_clean = wx.RadioButton( sbSizer_modus.GetStaticBox(), wx.ID_ANY, u"Reinigen", wx.DefaultPosition, wx.DefaultSize, 0 )
                bSizer6.Add( self.m_radio_clean, 0, wx.ALL|wx.EXPAND, 5 )
                #self.m_radio_clean.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )
                self.m_radio_clean.Bind(wx.EVT_LEFT_DOWN, self.radio_clean)
                
                sbSizer_modus.Add( bSizer6, 1, wx.EXPAND, 5 )

                self.m_panel7 = wx.Panel( sbSizer_modus.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
                sbSizer_modus.Add( self.m_panel7, 0, wx.ALL|wx.EXPAND, 2 )



                #Volumensection------------------------------------------------------
                sbSizer_volumen = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Volumen gesamt" ), wx.VERTICAL )
                
                    #Volumen --------------------------------------------------------
                self.m_textCtrl_volume = wx.TextCtrl( sbSizer_volumen.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 180,-1 ), wx.TE_CENTRE|wx.TE_READONLY )
                sbSizer_volumen.Add( self.m_textCtrl_volume, 1, wx.ALL|wx.EXPAND, 5 )
                self.m_textCtrl_volume.SetBackgroundColour( 'green' )
                self.m_panel_vol = wx.Panel(sbSizer_volumen.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
                sbSizer_volumen.Add( self.m_panel_vol, 0, wx.ALL|wx.EXPAND, 3 )
                #self.m_textCtrl_volume.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )

                self.m_panel_mod_vol = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
                
                bSizer_mod_vol.Add( sbSizer_modus, 0, wx.ALL|wx.EXPAND, 5 )
                bSizer_mod_vol.Add( self.m_panel_mod_vol, 1, wx.ALL|wx.EXPAND, 5 )
                bSizer_mod_vol.Add( sbSizer_volumen, 0, wx.ALL|wx.EXPAND, 5 )

                bSizer_main.Add( bSizer_mod_vol, 0, wx.ALL|wx.EXPAND, 5 )
                
                self.m_staticline31 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
                bSizer_main.Add( self.m_staticline31, 0, wx.EXPAND |wx.ALL, 5 )  



                #Start/Stopp section ------------------------------------------------
                sbSizer_start = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Start / Stopp" ), wx.VERTICAL )
                
                bSizer7 = wx.BoxSizer( wx.HORIZONTAL )
                
                self.m_button_start = wx.Button( sbSizer_start.GetStaticBox(), wx.ID_ANY, u"Start", wx.DefaultPosition, wx.DefaultSize, 0 )
                #self.m_button_start.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )
                self.m_button_start.SetToolTipString( u"Start des Modus mit voreingestellten Parametern" )
                #self.m_button_start.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), 70, 90, 90, False, wx.EmptyString ) )
                self.m_button_start.SetForegroundColour( wx.Colour( 9, 125, 2 ) )
                self.m_button_start.SetMinSize( wx.Size( -1,40 ) )
                self.m_button_start.SetMaxSize( wx.Size( -1,40 ) )
                self.m_button_start.Bind(wx.EVT_BUTTON, self.on_start)
                
                bSizer7.Add( self.m_button_start, 1, wx.ALL, 5 )
                
                self.m_button_stopp = wx.Button( sbSizer_start.GetStaticBox(), wx.ID_ANY, u"Stopp", wx.DefaultPosition, wx.DefaultSize, 0 )
                #self.m_button_stopp.SetFont( wx.Font( 9, 74, 90, 90, False, "Segoe UI" ) )
                self.m_button_stopp.SetToolTipString( u"Unterbricht den Modus" )
                self.m_button_stopp.SetForegroundColour( wx.Colour( 225, 0, 0 ) )
                self.m_button_stopp.SetMinSize( wx.Size( -1,40 ) )
                self.m_button_stopp.SetMaxSize( wx.Size( -1,40 ) )
                self.m_button_stopp.Enable( False )
                self.m_button_stopp.Bind(wx.EVT_BUTTON, self.on_stop)
                
                bSizer7.Add( self.m_button_stopp, 1, wx.ALL, 5 )
                
                
                sbSizer_start.Add( bSizer7, 1, wx.EXPAND, 5 )
                
                self.m_panel8 = wx.Panel( sbSizer_start.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
                sbSizer_start.Add( self.m_panel8, 0, wx.EXPAND |wx.ALL, 5 )
                
                
                bSizer_main.Add( sbSizer_start, 0, wx.ALL|wx.EXPAND, 5 )
                
                self.m_staticline32 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
                bSizer_main.Add( self.m_staticline32, 0, wx.EXPAND |wx.ALL, 5 )  


                

                #Serialcontroll section ---------------------------------------------
                sbSizer_serial = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Serial Control" ), wx.VERTICAL )
                
                sbSizer_serial.SetMinSize( wx.Size( -1,60 ) ) 
                bSizer8 = wx.BoxSizer( wx.HORIZONTAL )
                
                m_comboBox_comChoices = [ "" ]
                self.m_comboBox_com = wx.ComboBox( sbSizer_serial.GetStaticBox(), wx.ID_ANY, u"COM", wx.DefaultPosition, wx.DefaultSize, m_comboBox_comChoices, 0 )
                bSizer8.Add( self.m_comboBox_com, 0, wx.ALL, 5 )
                self.m_comboBox_com.SetItems(portlist)
                self.m_comboBox_com.SetSelection( 0 )
                self.m_comboBox_com.Bind(wx.EVT_COMBOBOX, self.choice_focus)
                
                m_comboBox_baudChoices = [ u"9600", u"19200", u"38400", u"57600", u"115200" ]
                self.m_comboBox_baud = wx.ComboBox( sbSizer_serial.GetStaticBox(), wx.ID_ANY, u"baud", wx.DefaultPosition, wx.DefaultSize, m_comboBox_baudChoices, 0 )
                self.m_comboBox_baud.SetSelection( 3 )
                self.m_comboBox_baud.Bind(wx.EVT_COMBOBOX, self.choice_focus)
                bSizer8.Add( self.m_comboBox_baud, 0, wx.ALL, 5 )        
                

                    #Serial TextCtrl -------------------------------------------
                self.m_textCtrl_serial = wx.TextCtrl( sbSizer_serial.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
                bSizer8.Add( self.m_textCtrl_serial, 1, wx.ALL, 5 )
                
                sbSizer_serial.Add( bSizer8, 1, wx.EXPAND, 5 )    

                        #Aktualiseren Button -----------------------------------
                self.aktualisieren = wx.Button( sbSizer_serial.GetStaticBox(), wx.ID_ANY, u"aktualisieren", wx.DefaultPosition, wx.DefaultSize, 0 )
                sbSizer_serial.Add( self.aktualisieren, 1, wx.ALL|wx.EXPAND, 5 )
                self.aktualisieren.Bind(wx.EVT_BUTTON, self.akt_action)

                self.m_panel9 = wx.Panel( sbSizer_serial.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
                sbSizer_serial.Add( self.m_panel9, 0, wx.EXPAND |wx.ALL, 2 )
                
                bSizer_main.Add( sbSizer_serial, 0, wx.ALL|wx.EXPAND, 5 )
                
                self.SetSizer( bSizer_main )
                self.Layout()
                
                self.Centre( wx.BOTH )

                #Startup section
                self.m_radio_pulse.SetValue( True )
                self.m_textCtrl_volume.Enable( False )
                self.timer = wx.Timer(self)
                self.Bind(wx.EVT_TIMER, self.show_puls, self.timer)

                if portlist != []:
                        ser.port = self.m_comboBox_com.GetString(self.m_comboBox_com.GetSelection())
                        ser.baudrate = int(self.m_comboBox_baud.GetString(self.m_comboBox_baud.GetSelection()))
                        ser.open()
                        if ser.is_open:
                                serstring = ser.readline()
                                #print(serstring)
                                ser.write('con')
                                time.sleep(0.05)
                                ser.write('pul')
                                self.m_statusBar.PushStatusText("\tVerbunden", 0)
                                serplit = serstring.split(",")
                                self.m_text_on.SetValue((serplit[0]))
                                self.m_text_off.SetValue((serplit[1]))
                                self.m_text_pulse.SetValue((serplit[2]))
                                self.m_textCtrl_volume.SetValue(str(round((4.2667+0.89261*int(serplit[0]))*int(serplit[2]),1))+u" µl"+" "+ unichr(177)+ " "+ str(2*int(serplit[2]))+u" µl")
                        self.aktualisieren.Enable( False )
                        self.m_textCtrl_volume.Enable( True )
                elif portlist == []:
                        self.m_comboBox_com.Enable( False )
                        self.m_comboBox_baud.Enable( False )
                        self.m_textCtrl_serial.WriteText(" System nicht verbunden\n")
                        self.m_textCtrl_serial.Enable( False )
                        self.m_button_start.Enable( False )
                        self.m_button_stopp.Enable( False )
                        self.m_radio_pulse.Enable( False )
                        #self.m_radio_menge.Enable( False )
                        self.m_radio_clean.Enable( False )
                        self.m_text_pulse.Enable( False )
                        self.m_text_on.Enable( False )
                        self.m_text_off.Enable( False )
                        self.m_button_speichern.Enable( False )
                        self.m_statusBar.PushStatusText("\tNicht verbunden", 0)

        def prep_open( self, parent ):
                self.fr = wx.Frame(None, title='Präparationgerade', id = wx.ID_ANY, pos = wx.DefaultPosition,size=wx.Size(880, 650),style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)
                self.fr.SetSizeHintsSz( wx.Size( 880,650 ), wx.Size( 880,650 ) )
                self.panel = PrepWindow(self.fr)
                if ser.isOpen():
                    x_val = int(self.m_text_on.GetValue())
                    y_val = (4.2667+0.89261*x_val)
                    if x_val > 100:
                        self.panel.draw(500)
                        self.panel.draw_point(x_val)
                        self.panel.m_slider_x.SetValue(x_val)
                        self.panel.m_slider_y.SetValue(y_val)
                        self.panel.m_text_diff_slider_x.SetLabel(str(self.m_text_on.GetValue())+ " ms")
                        self.panel.m_text_diff_slider_y.SetLabel(str(round(y_val,1))+ u" µl")
                    elif x_val < 100:
                        self.panel.draw(110)
                        self.panel.draw_point(x_val)
                        self.panel.m_slider_x.SetValue(x_val)
                        self.panel.m_slider_y.SetValue(y_val)
                        self.panel.m_text_diff_slider_x.SetLabel(str(self.m_text_on.GetValue())+ " ms")
                        self.panel.m_text_diff_slider_y.SetLabel(str(round(y_val,1))+ u" µl")                        
                else:
                    self.panel.draw(110)
                    self.panel.draw_point(10)
                self.fr.Show()
                self.fr.Center()
                self.fr.SetIcon(icon.iconset.GetIcon())
                self.panel.m_sdbSizer_Cancel.Bind(wx.EVT_BUTTON, self.OnClose_Volumen)
                self.panel.m_sdbSizerOK.Bind(wx.EVT_BUTTON, self.onOkay)

        def __del__( self ):
                pass

        def on_timer(event):
                pass  # do whatever

        def onOkay(self,event):
                if ser.isOpen():
                    pul_val = self.panel.global_ret()
                    self.m_text_on.SetValue(str(pul_val))
                    self.onEnter_ont(event)
                    #self.m_textCtrl_volume.SetValue(str(round((4.2667+0.89261*pul_val)*int(self.m_text_pulse.GetValue()),1))+" "+ unichr(177)+ " "+ str(2*int(self.m_text_pulse.GetValue()))+u" µl")
                self.fr.Destroy()

        def OnClose(self, event):  # wxGlade: Main.<event_handler>
                self.Destroy()
                event.Skip()
                ser.close()
                
        def OnClose_Volumen(self, event):
                self.fr.Destroy()

        def OnAbout(self, event):
                dlg = AboutBox()
                dlg.ShowModal()
                dlg.Destroy()

        def radio_pulse(self, event):
                self.m_textCtrl_volume.Enable( False )
                event.GetEventObject().SetValue(not event.GetEventObject().GetValue())   
                ser.write('pul')
                time.sleep(0.05)
                ser.write('fla'+str(self.m_text_pulse.GetValue()))
                time.sleep(0.05)   
                ser.write('ont'+str(self.m_text_on.GetValue()))
                time.sleep(0.05)
                ser.write('oft'+str(self.m_text_off.GetValue()))
                self.m_text_pulse.Enable( True )
                self.m_textCtrl_volume.Enable( True )
                self.m_text_on.Enable( True )
                self.m_text_off.Enable( True )
                self.m_button_speichern.Enable( True )
                
        def radio_clean(self, event):
                self.m_textCtrl_volume.Enable( False )
                event.GetEventObject().SetValue(not event.GetEventObject().GetValue())
                ser.write('cle')
                time.sleep(0.05)
                ser.write('fla-1')
                time.sleep(0.05)   
                ser.write('ont50')
                time.sleep(0.05)
                ser.write('oft50')
                self.m_text_pulse.Enable( False )
                self.m_text_on.Enable( False )
                self.m_text_off.Enable( False )
                self.m_button_speichern.Enable( False )

        #Startbutton action
        def on_start(self,event):
            if self.m_radio_pulse.GetValue() == 1:
                ser.write('sta')
                self.m_statusBar.PushStatusText("\tPräparation läuft...", 0)
                self.m_statusBar.PushStatusText(" \tPuls: 0", 1)
                self.flash = int(self.m_text_pulse.GetValue())
                ontval = self.m_text_on.GetValue()
                oftval = self.m_text_off.GetValue()
                interval = (int(ontval) + int(oftval))
                self.timer.Start(interval)
                self.count = 0
                self.progress_bar.SetValue(0)
                self.progress_bar.SetRange(self.flash)
                self.progress_bar.Show()
                #self.m_textCtrl_volume.Enable( False )
                self.m_text_pulse.Enable( False )
                self.m_text_on.Enable( False )
                self.m_text_off.Enable( False )
                self.m_button_speichern.Enable( False )
                self.m_radio_pulse.Enable( False )
                #self.m_radio_menge.Enable( False )
                self.m_radio_clean.Enable( False )
                self.m_button_start.Enable( False )
                self.m_button_stopp.Enable( True )
                
            elif self.m_radio_clean.GetValue() == 1:
                ser.write('sta')
                self.m_statusBar.PushStatusText("\tReinigung läuft...", 0)
                self.m_statusBar.PushStatusText(" ", 1)
                self.m_statusBar.PushStatusText(" ", 2)
                self.m_textCtrl_volume.Enable( False )
                self.m_text_pulse.Enable( False )
                self.m_text_on.Enable( False )
                self.m_text_off.Enable( False )
                self.m_button_speichern.Enable( False )
                self.m_radio_pulse.Enable( False )
                #self.m_radio_menge.Enable( False )
                self.m_radio_clean.Enable( False )
                self.m_button_start.Enable( False )
                self.m_button_stopp.Enable( True )

        def on_stop(self,event):
                ser.write('sto')
                self.m_statusBar.PushStatusText(" gestoppt", 0)
                self.timer.Stop()
                if self.m_radio_pulse.GetValue() == 1:
                    self.m_text_pulse.Enable( True )
                    self.m_text_on.Enable( True )
                    self.m_text_off.Enable( True )
                    self.m_button_speichern.Enable( True )
                    self.m_radio_pulse.Enable( True )
                    #self.m_radio_menge.Enable( True )
                    self.m_radio_clean.Enable( True )
                    self.m_textCtrl_volume.Enable( True )
                    self.m_button_start.Enable( True )
                if self.m_radio_clean.GetValue() == 1:
                    self.m_button_start.Enable( True )
                    self.m_radio_pulse.Enable( True )
                    #self.m_radio_menge.Enable( True )
                    self.m_radio_clean.Enable( True )
                self.progress_bar.Hide()
                self.m_statusBar.PushStatusText(" ", 2)
                self.m_button_stopp.Enable( False )

        def choice_focus(self,event):
                ser.close()
                ser.port = self.m_comboBox_com.GetString(self.m_comboBox_com.GetSelection())
                ser.baudrate = int(self.m_comboBox_baud.GetString(self.m_comboBox_baud.GetSelection()))
                ser.open()
                if ser.is_open:
                    #print('connected')
                    serstring = ser.readline()
                    ser.write('pul')
                    serplit = serstring.split(",")
                    self.m_text_on.SetValue((serplit[0]))
                    self.m_text_off.SetValue((serplit[1]))
                    self.m_text_pulse.SetValue((serplit[2]))
                    self.m_button_start.Enable( True )
                    self.m_textCtrl_volume.Enable( True )
                    self.m_radio_pulse.Enable( True )
                    #self.m_radio_menge.Enable( True )
                    self.m_radio_clean.Enable( True )
                    self.m_text_pulse.Enable( True )
                    self.m_text_on.Enable( True )
                    self.m_text_off.Enable( True )
                    self.m_button_speichern.Enable( True )                    
                    self.m_textCtrl_volume.SetValue(str(round((4.2667+0.89261*int(serplit[0]))*int(serplit[2]),1))+u" µl"+" "+ unichr(177)+ " "+ str(2*int(serplit[2]))+u" µl")
                    #time.sleep(0.05)
                    ser.write('con')
                    self.m_statusBar.PushStatusText("\tVerbunden", 0)                    
                    self.m_textCtrl_serial.Clear() 

        def show_puls(self,event):
                self.m_statusBar.PushStatusText(" Präparation läuft...", 0)
                self.m_statusBar.PushStatusText(" \tPuls: "+ str(self.count+1), 1)
                self.progress_bar.SetValue(self.count+1)
                self.count += 1
                if self.count == self.flash:
                    #self.m_textCtrl_volume.Enable( False )
                    self.m_text_pulse.Enable( True )
                    self.m_text_on.Enable( True )
                    self.m_text_off.Enable( True )
                    self.m_button_speichern.Enable( True )
                    self.m_radio_pulse.Enable( True )
                    #self.m_radio_menge.Enable( True )
                    self.m_radio_clean.Enable( True )
                    self.m_button_start.Enable( True )
                    self.m_button_stopp.Enable( False )
                    self.m_statusBar.PushStatusText(" ", 0)
                    self.m_statusBar.PushStatusText(" \tPulse = "+ str(self.flash), 1)
                    self.progress_bar.Hide()
                    self.m_statusBar.PushStatusText(" ", 2)
                    self.timer.Stop()
                
        def akt_action(self,event):
                portlist = []
                portlist = serial_ports()
                ser = serial.Serial()
                    
                if portlist != []:
                    self.m_comboBox_com.SetItems(portlist)
                    self.m_comboBox_com.SetSelection( 0 )
                    ser.port = self.m_comboBox_com.GetString(self.m_comboBox_com.GetSelection())
                    ser.baudrate = int(self.m_comboBox_baud.GetString(self.m_comboBox_baud.GetSelection()))
                    self.m_comboBox_com.Enable( True )
                    self.m_comboBox_baud.Enable( True )
                    self.m_textCtrl_serial.Clear()
                    self.m_textCtrl_serial.Enable( True )
                    #self.m_statusBar.PushStatusText("Verbunden", 0)
                    self.aktualisieren.Enable( False )
                    self.m_textCtrl_serial.WriteText(" COM Port aus der Liste wählen \n")
                elif portlist == []:
                    self.m_comboBox_com.Enable( False )
                    self.m_comboBox_baud.Enable( False )
                    self.m_textCtrl_serial.Clear()
                    self.m_textCtrl_serial.WriteText(" System nicht verbunden\n")
                    self.m_textCtrl_serial.Enable( False )
                    self.m_button_start.Enable( False )
                    self.m_button_stopp.Enable( False )
                    self.m_radio_pulse.Enable( False )
                    #self.m_radio_menge.Enable( False )
                    self.m_radio_clean.Enable( False )
                    self.m_text_pulse.Enable( False )
                    self.m_text_on.Enable( False )
                    self.m_text_off.Enable( False )
                    self.m_button_speichern.Enable( False )
                    self.m_statusBar.PushStatusText("\tNicht verbunden", 0)

#----------------------------------------------------------------------
        def onEnter_ont(self, event):
                ont = self.m_text_on.GetValue()
                ser.write('ont'+str(ont))
                ontstr = "T_on: " + str(ont)+ " ms"
                time.sleep(0.05)
                
                oft = self.m_text_off.GetValue()
                oftstr = "T_off: " + str(oft)+ " ms"
                ser.write('oft'+str(oft))
                time.sleep(0.05)
                
                flashnum = self.m_text_pulse.GetValue()
                ser.write('fla'+str(flashnum))
                flastr = "Pulse: " + str(flashnum)
                time.sleep(0.05)
                
                ser.write('spe')
                self.m_statusBar.PushStatusText(" \t" + ontstr, 0)
                self.m_statusBar.PushStatusText( "\t" + oftstr, 1)
                self.m_statusBar.PushStatusText("\t" + flastr, 2)

                pul_val = int(self.m_text_on.GetValue())
                self.m_textCtrl_volume.SetValue(str(round((4.2667+0.89261*pul_val)*int(self.m_text_pulse.GetValue()),1))+u" µl"+" "+ unichr(177)+ " "+ str(2*int(self.m_text_pulse.GetValue()))+u" µl")

                
                #keycode = event.GetKeyCode()
                #if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER or keycode == wx.WXK_TAB:
                    #self.process_text(event=None)
                #    event.EventObject.Navigate()
                #event.Skip()
                
        def OnAboutBox(self, e):
            
                info = wx.AboutDialogInfo()
                #info.SetSizeHintsSz( wx.Size( 300,200 ), wx.Size( 300,200 ) )

                aboutText = "It was designed for the in-situ preparation\n of Mn6Cr Single Molecule Magnets.\n It is running on wxPython and Python."
                info.SetIcon(wx.Icon('icon.png', wx.BITMAP_TYPE_PNG))
                info.Name = 'Pulse Injection Control'
                info.Version = '1.2'
                info.Description = aboutText
                info.WebSite = ("http://wiki.wxpython.org", "wxPython Wiki")
                info.SetCopyright('(C) 2017 Timm Volkmann')
                #info.AddDeveloper('Timm Volkmann'
    
                wx.AboutBox(info)
                
                    
#####################################################################################                
if __name__ == '__main__':

    #try:
    portlist = []
    portlist = serial_ports()
    ser = serial.Serial()
    
    app = wx.App(redirect=True)   # Error messages go to popup window
    top = MainFrame(u"Pulse Injection Control")
    top.Show()
    app.MainLoop()

