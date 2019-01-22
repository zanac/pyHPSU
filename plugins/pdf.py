#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# requires reportlab, time, configparser, os, sys, pil

# config inf conf_file (defaults):
# [PDF]
# FILE_PATH = "__the__users__homedir__"
# FILE_NAME = "settings.pdf"

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm,mm
from operator import itemgetter
from pathlib import Path
import time
import configparser
import os
import sys



class export():
    hpsu = None
    def __init__(self, hpsu=None, logger=None, config_file=None):
        self.page_height=defaultPageSize[1]
        self.page_width=defaultPageSize[0]
        self.styles = getSampleStyleSheet()
        self.title = "pyHPSU settings"
        self.pageinfo = "pyHPSU ver. 1.?"
        self.creation_time = time.asctime()
        self.logo = "/usr/share/pyHPSU/pyHPSU-logo.png"

        self.hpsu = hpsu
        self.logger = logger
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.config_file):
            self.config.read(self.config_file)
        else:
            sys.exit(9)

        # Path to save the pdf file
        if self.config.has_option('PDF', 'FILE_PATH'):
            self.file_path = self.config['FHEM']['FILE_PATH']
        else:
            self.file_path = str(Path.home())

        # Filename to save the pdf file
        if self.config.has_option('PDF', 'FILE_NAME'):
            self.file_name = self.config['FHEM']['FILE_NAME']
        else:
            self.file_name = "settings.pdf"
 

    def myFirstPage(self,canvas, doc):
        canvas.saveState()
        canvas.drawImage("/usr/share/pyHPSU/pyHPSU-logo.jpg",cm,self.page_height-(2.5*cm),width=5*cm,height=5*cm,mask=None, preserveAspectRatio=True,anchor="sw")
        #canvas.rect(self.page_width-(1*cm),self.page_height-(5*cm),width=10*cm,height=5*cm)
        canvas.setFont('Helvetica-Bold',16)
        canvas.drawCentredString(self.page_width/2.0, self.page_height-50, self.title)
        #canvas.line(cm,self.page_height-50,self.page_width,self.page_height-50)
        canvas.setFont('Helvetica',9)
        canvas.drawString(cm, 0.75 * cm,"Page 1")
        canvas.drawCentredString(self.page_width/2.0, 0.75 * cm, self.pageinfo)
        canvas.drawRightString(self.page_width-cm,0.75 * cm, self.creation_time)
        canvas.restoreState()

    def myLaterPages(self,canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(cm, 0.75 * cm,"Page %d" % (doc.page))
        canvas.drawCentredString(self.page_width/2, 0.75 * cm, self.pageinfo)
        canvas.drawRightString(self.page_width-cm,0.75 * cm, self.creation_time)
        canvas.restoreState()





    def pushValues(self, vars=None):
        self.file=self.file_path + "/" + self.file_name
        doc = SimpleDocTemplate(self.file)
        Story = [Spacer(1,2*cm)]
        style = self.styles["Normal"]
        sorted_vars=sorted(vars, key=itemgetter('name'))
        data=[["Name","current value","writeable"]]
        for r in sorted_vars:
            name=r["name"]
            if self.hpsu.command_dict[name]["writable"]=="true":
                writable="yes"
            else:
                writable="no"

            d=[r["name"],r["resp"],writable]
            data.append(d)
            t=Table(data,colWidths=(50*mm,50*mm,20*mm))

            t.setStyle(TableStyle([('ALIGN',(1,1),(-1,-1),'LEFT'),
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                       ]))
            #if self.hpsu.command_dict[name]["writable"]=="true":
            #bogustext = ("%-20s - %-10s" % (r["name"], r["resp"])) 
            #p = Paragraph(bogustext, style)
            #Story.append(p)
            #Story.append(Spacer(1,0.2*cm))
            
        Story.append(t)
        doc.build(Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)

    
        


    if __name__ == '__main__':
        app = export()

        app.exec_()


    