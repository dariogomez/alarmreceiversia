#!/usr/bin/python
# -*- coding: utf-8 -*- 

import logging
import threading
import re
import time
import smtplib
import httplib
from email.mime.text import MIMEText
from ADB import ADB

DISABLE_SMS=True
adb=ADB("/opt/android-sdk-linux_x86/platform-tools/adb")


# CL-OP -> Inserimento totale
# NL-OP -> Inserimento parziale
# BC -> Reset memoria
# JP -> Riconoscimento codice/chiave
# XT-XR -> Resistenza interna batteria
# YM-YR -> Corto circuito/disconnessione batteria
# YT-YR -> Batteria inefficiente
# AT-AR -> Mancanza alimentazione
# EM-EN -> Scomparsa dispositivo
# DD-DR -> Codice/chiave errati
# LB-LX -> Ingresso programmazione
# OU-OV -> Malfunzionamento uscita

class AlarmManager:
    alarmPattern = re.compile(r"\[#[0-9]{6}\|....(..)[0-9]+\^?(.*)\^?\]")
        
    def __init__(self):
        self.alarmActive = False
        self.threadLock = threading.Lock()
        self.reactions = {            
            # Non definito
            "UX" : {"subject": "Non definito", "execute": None},
            
            # Set
            "BA" : {"subject": "ALLARME INTRUSIONE", "execute": self.inviaSmsEdEmail},
            "TA" : {"subject": "SABOTAGGIO", "execute": self.inviaSmsSeInseritoEdEmail},
            "BB" : {"subject": "Esclusione", "execute": self.sendEmail},
            "CL" : {"subject": "Inserimento totale", "execute": self.inserimentoAllarme},
            "NL" : {"subject": "Inserimento parziale", "execute": self.inserimentoAllarme},
            "BC" : {"subject": "Reset memoria", "execute": self.sendEmail},
            "JP" : {"subject": "Riconoscimento codice/chiave", "execute": self.sendEmail},
            "XT" : {"subject": "Resistenza interna batteria", "execute": self.sendEmail},
            "YM" : {"subject": "Corto circuito/disconnessione batteria", "execute": self.sendEmail},
            "YT" : {"subject": "Batteria inefficiente", "execute": self.sendEmail},
            "AT" : {"subject": "Mancanza alimentazione", "execute": self.sendEmail},
            "EM" : {"subject": "Scomparsa dispositivo", "execute": self.sendEmail},
            "DD" : {"subject": "Codice/chiave errati", "execute": self.sendEmail},
            "LB" : {"subject": "Ingresso programmazione", "execute": self.sendEmail},
            "OU" : {"subject": "Malfunzionamento uscita", "execute": self.inviaSmsSeEmailNonFunziona},
            
            # Reset
            "BR" : {"subject": "Ripristino allarme intrusione", "execute": self.sendEmail},
            "TR" : {"subject": "Ripristino sabotaggio", "execute": self.sendEmail},
            "BU" : {"subject": "Ripristino esclusione", "execute": self.sendEmail},
            "OP" : {"subject": "Disinserimento", "execute": self.disinserimentoAllarme},
            "XR" : {"subject": "Ripristino resistenza interna batteria", "execute": self.sendEmail},
            "YR" : {"subject": "Ripristino batteria", "execute": self.sendEmail},
            "AR" : {"subject": "Ripristino alimentazione", "execute": self.sendEmail},
            "EN" : {"subject": "Ripristino scomparsa dispositivo", "execute": self.sendEmail},
            "DR" : {"subject": "Ripristino codice/chiave errati", "execute": self.sendEmail},
            "LX" : {"subject": "Uscita programmazione", "execute": self.sendEmail},
            "OV" : {"subject": "Ripristino malfunzionamento uscita", "execute": self.inviaSmsSeEmailNonFunziona}
        }
        
    def manageAlarmMessage(self, msg):
        m = AlarmManager.alarmPattern.search(msg)
        if m:
            tipo = m.group(1)
            desc = m.group(2).strip()
            logging.info("Tipo evento: " + tipo + ", testo: " + desc)
            
            if tipo in self.reactions:
                reaction = self.reactions[tipo]
                subject = reaction["subject"]
                message = subject + ": " + desc
                executeMethod = reaction["execute"]
                if executeMethod:
                    executeMethod(subject, message)
            else:
                logging.warn("Evento sconosciuto: " + tipo + ": " + desc)
            
            return
    
    def inserimentoAllarme(self, subject, message):
        self.alarmActive = True
        AlarmManager.callPiServer("allOff/group:1")
        
        self.sendEmail(subject, message)
        AlarmManager.callTaskerTask("Abilita_Cell")
    
    def disinserimentoAllarme(self, subject, message):
        self.alarmActive = False
        AlarmManager.callPiServer("allOn/group:1")
            
        self.sendEmail(subject, message)
        AlarmManager.callTaskerTask("Disabilita_Cell")
    
    def inviaSmsEdEmail(self, subject, message):
        self.sendSms(message)
        self.sendEmail(subject, message)
        
    def inviaSmsSeInseritoEdEmail(self, subject, message):
        if self.alarmActive:
            self.sendSms(message)
            
        self.sendEmail(subject, message)        
    
    def inviaSmsSeEmailNonFunziona(self, subject, message):
        if self.alarmActive:
            self.sendSms(message)
            
        self.sendEmail(subject, message)
        
    def sendEmail(self, subject, msg):
        # Get lock to synchronize threads
        logging.debug("Acquiring lock...")
        self.threadLock.acquire()
        
        logging.info("Invio email: " + msg)
        try:
            msg = MIMEText(msg)

            mailFrom = "Allarme Casa <videomozzi@gmail.com>"
            mailTo = "Roberto Mozzicato <bitblasters@gmail.com>"
            msg['Subject'] = subject
            msg['From'] = mailFrom
            msg['To'] = mailTo
    
            server = smtplib.SMTP('smtp.gmail.com:587')
            server.starttls()
            server.login("videomozzi","pwdmarcia*123")
            server.sendmail(mailFrom, [mailTo], msg.as_string())
            server.quit()
            
            return True
        except Exception as e:
            logging.error("Errore durante l'invio dell'email: " + str(e))
            return False
        finally:        
            # Free lock to release next thread
            self.threadLock.release()
            logging.debug("Lock released!")
        
    def sendSms(self, msg):
        logging.info("Invio sms: " + msg)
        if DISABLE_SMS:
            logging.info("sms disabled")
            return
        
        # Get lock to synchronize threads
        logging.debug("Acquiring lock...")
        self.threadLock.acquire()
        
        # Free lock to release next thread
        self.threadLock.release()
        logging.debug("Lock released!")
    
    @staticmethod
    def callTaskerTask(taskName, par1=None, par2=None, par3=None):
        command = "am broadcast -a pl.bossman.taskerproxy.ACTION_TASK --es task_name " + taskName
        
        if par1:
            command += " --es p1 " + par1
        if par2:
            command += " --es p2 " + par2
        if par3:
            command += " --es p3 " + par3
             
        sendAdbCommand(command)
        
    @staticmethod
    def sendAdbCommand(command):
        adb.start_server()
        adb.shell_command(command)
    
    @staticmethod
    def callPiServer(requestString):
        requestString = requestString + "?client=raspberry&time=" + str(int(time.time()));
        conn = httplib.HTTPConnection(config['pi_server_url'])
        conn.request("GET", "/" + encrypt(requestString))
        r1 = conn.getresponse()
        print(r1.status, r1.reason)
        
    @staticmethod
    def encrypt(message):
        cipher = Blowfish.new(config['encrypt_passphrase'], Blowfish.MODE_CBC, config['encrypt_iv'])
        pad = 8-(len(message)%8)
        for x in range(pad):
            message+=" "
        encrypted = cipher.encrypt(message)
        return base64.urlsafe_b64encode(encrypted)

if __name__ == "__main__":
    alarmManager = AlarmManager()
    s = '"SIA-DCS"0091L0#001234[#001234|Nri0CL0]_06:43:58,02-15-2015'
    alarmManager.manageAlarmMessage(s)