# -*- coding: utf-8 -*-

import urllib2, httplib
import json
import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('data/Smarter-HPSU.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

logger.info('WU Start')

WU_API_KEY = '14cd099d84ae0366'
WU_COUNTRY = 'Italy'
WU_LOCATION = 'Vigevano'
WU_APIURL = 'http://api.wunderground.com/api/' + WU_API_KEY + '/hourly/q/' + WU_COUNTRY + '/' + WU_LOCATION + '.json' 

try:
	logger.debug(WU_APIURL)
	f = urllib2.urlopen(WU_APIURL)
except urllib2.HTTPError, e:
	logger.error('HTTPError = ' + str(e.code))
	quit()
except urllib2.URLError, e:
	logger.error('URLError = ' + str(e.reason))
	quit()
except httplib.HTTPException, e:
	logger.error('HTTPException')
	quit()
except Exception:
	logger.error('generic exception: ' + traceback.format_exc())
	quit()

try:
	json_string = f.read()
except Exception:
        logger.error('generic exception: ' + traceback.format_exc())
        quit()

logger.info('WU End')

try:
	parsed_json = json.loads(json_string)
except Exception:
        logger.error('generic exception: ' + traceback.format_exc())
        quit()

logger.debug(parsed_json)

temperatura_esterna_avg24 = 0.0
umidita_esterna_avg24 = 0.0
temperatura_esterna_max24 = -50.0
temperatura_esterna_min24 = 50.0
temperatura_esterna_delta24 = 0.0
temperatura_esterna_median24 = 0.0

conta = 0

temp_mandata_legacy = 0.0
temp_mandata_smart = 0.0

temp_interna_setpoint = 20.5
curva_climatica = 0.5

temp_esterna_corrente = 0.0
umidita_esterna_corrente = 0.0

# parametri modello di controllo - start

K_offset_temp_esterna = -0.5
K_delta_temp_esterna_superiore = 0.5
K_delta_temp_esterna_inferiore = 0.8
K_delta_umidita_esterna = 0.005
K_min_delta_temp_off = 5.5
K_max_time_off = 21.0 / 100.0 
K_min_mandata = 25.0

# parametri modello di controllo - end

COP_legacy = 0.0
COP_smart = 0.0

logger.info('Next 24 hours average evaluation start')

for previsione_oraria in parsed_json['hourly_forecast']:
		if (conta < 24):
			logging.info ( previsione_oraria['FCTTIME']['hour_padded'] + ' T = ' + previsione_oraria['temp']['metric'] + ' C ; HR = ' + previsione_oraria['humidity'] + ' %')
			temperatura_esterna_avg24 += float(previsione_oraria['temp']['metric'].replace(u'\N{MINUS SIGN}', '-')) + K_offset_temp_esterna
			umidita_esterna_avg24 += float(previsione_oraria['humidity'].replace(u'\N{MINUS SIGN}', '-'))
			temperatura_esterna_max24 = max (temperatura_esterna_max24, float(previsione_oraria['temp']['metric'].replace(u'\N{MINUS SIGN}', '-')) + K_offset_temp_esterna)
			temperatura_esterna_min24 = min (temperatura_esterna_min24, float(previsione_oraria['temp']['metric'].replace(u'\N{MINUS SIGN}', '-')) + K_offset_temp_esterna)
			conta += 1

temperatura_esterna_avg24 /= 24.0
umidita_esterna_avg24 /= 24.0
temperatura_esterna_delta24 = temperatura_esterna_max24 - temperatura_esterna_min24
temperatura_esterna_median24 = (temperatura_esterna_min24 + temperatura_esterna_max24) / 2.0

logger.info('Next 24 hours average evaluation end')

print "WEATHER FORECAST => Weather Underground Temperature Offset % 2.1f C" % (K_offset_temp_esterna)
print "WEATHER FORECAST => Next 24 hours temperature Min % 2.1f C / Avg % 2.1f C / Max % 2.1f C" % (temperatura_esterna_min24, temperatura_esterna_avg24, temperatura_esterna_max24)
print "WEATHER FORECAST => Next 24 hours temperature Median % 2.1f C" % (temperatura_esterna_median24)
print "WEATHER FORECAST => Next 24 hours humidty Avg % 2.0f %%" % (umidita_esterna_avg24)

print "SMART MODEL      => On/Off control Min delta temperature {0:2.1f} C".format(K_min_delta_temp_off)
print "SMART MODEL      => Max Off time is {0:2.0f} % ({1:2.1f} hours)".format(K_max_time_off * 100, K_max_time_off * 24.0)

print "SMART CONTROL    => Off threshold temperature {0:2.1f} C".format(temperatura_esterna_min24 + K_max_time_off * (temperatura_esterna_median24 - temperatura_esterna_min24))

gradi_mandata_legacy = 0.0
gradi_mandata_smart = 0.0

COP_totale_legacy = 0.0
COP_totale_smart = 0.0

conta = 0

for previsione_oraria in parsed_json['hourly_forecast']:
	if (conta < 24):

# calcola dati input per simulazione
	
		temp_esterna_corrente = float(previsione_oraria['temp']['metric']) + K_offset_temp_esterna
		umidita_esterna_corrente = float(previsione_oraria['humidity'])
		ora_corrente = previsione_oraria['FCTTIME']['pretty']

# climatica standard (basata solo su temperatura esterna corrente)

		temp_mandata_legacy = temp_interna_setpoint + curva_climatica * (temp_interna_setpoint - temp_esterna_corrente)

		COP_legacy = 122.69 * pow (temp_mandata_legacy - temp_esterna_corrente, -1.002)

# climatica Smart: baseline basata sulla previsione della temperatura media esterna per le 24 ore successive

		DT1 = temp_interna_setpoint + curva_climatica * (temp_interna_setpoint - temperatura_esterna_avg24)

# climatica Smart: correzione in base a temperatura esterna e setpoint interno (climatica inversa)

		if (temp_esterna_corrente >= temperatura_esterna_avg24):
			DT2 = K_delta_temp_esterna_superiore * (temp_esterna_corrente - temperatura_esterna_avg24)
		else:
			DT2 = K_delta_temp_esterna_inferiore * (temp_esterna_corrente - temperatura_esterna_avg24)

# climatica Smart: correzione in base a umidita' esterna per prevenire i defrost

		DT3 = K_delta_umidita_esterna * (umidita_esterna_avg24 - umidita_esterna_corrente)

		temp_mandata_smart = DT1 + DT2 + DT3

# climatica Smart: simula l'arrotondamento a 0.5 resente nell'impostazione della temperatura di mandata fissa oppure del setpoint di temperatura ambiente

		temp_mandata_smart = round (temp_mandata_smart * 2.0) / 2.0

		COP_smart = 122.69 * pow (temp_mandata_smart - temp_esterna_corrente, -1.002)

# climatica standard: se la temperatura di mandata e' inferiore al minimo ammesso, l'unita' esterna non si accende (cambieremo proprio modalita' di funzionamento)

		if (temp_mandata_legacy > K_min_mandata):
			gradi_mandata_legacy += temp_mandata_legacy - temp_interna_setpoint
			COP_totale_legacy += COP_legacy * (temp_mandata_legacy - temp_interna_setpoint)

# climatica Smart: verifica che non ci sono le condizioni per fare degli spegnimenti dell'unita' esterna per ottimizzare il COP

		if (temperatura_esterna_delta24 < K_min_delta_temp_off) or (temp_esterna_corrente >= temperatura_esterna_min24 + K_max_time_off * (temperatura_esterna_median24 - temperatura_esterna_min24)):

# climatica Smart: se la temperatura di mandata e' inferiore al minimo ammesso, l'unita' esterna non si accende (cambieremo proprio modalita' di funzionamento)

			if (temp_mandata_smart > K_min_mandata):
				gradi_mandata_smart += temp_mandata_smart - temp_interna_setpoint
				COP_totale_smart += COP_smart * (temp_mandata_smart - temp_interna_setpoint)

			if (temp_mandata_legacy > K_min_mandata):
				print "{0:25} T = {1:5.1f} HR = {2:2.0f} => HPSU ON  T mand = {3:4.1f} COP = {4:4.1f} DT = {5:4.1f} => SMART HPSU ON  T mand = {6:4.1f} ({7:+4.2f} {8:+4.2f} {9:+4.2f}) COP = {10:4.1f} DT = {11:4.1f}".format(ora_corrente, temp_esterna_corrente, umidita_esterna_corrente, temp_mandata_legacy, COP_legacy, temp_mandata_legacy - temp_interna_setpoint, temp_mandata_smart, DT1, DT2, DT3, COP_smart, temp_mandata_smart - temp_interna_setpoint)
			else:
				print "{0:25} T = {1:5.1f} HR = {2:2.0f} => HPSU OFF T mand = {3:4.1f} COP = {4:4.1f} DT = {5:4.1f} => SMART HPSU ON  T mand = {6:4.1f} ({7:+4.2f} {8:+4.2f} {9:+4.2f}) COP = {10:4.1f} DT = {11:4.1f}".format(ora_corrente, temp_esterna_corrente, umidita_esterna_corrente, temp_mandata_legacy, COP_legacy, temp_mandata_legacy - temp_interna_setpoint, temp_mandata_smart, DT1, DT2, DT3, COP_smart, temp_mandata_smart - temp_interna_setpoint)
		else:
			print "{0:25} T = {1:5.1f} HR = {2:2.0f} => HPSU ON  T mand = {3:4.1f} COP = {4:4.1f} DT = {5:4.1f} => SMART HPSU OFF".format(ora_corrente, temp_esterna_corrente, umidita_esterna_corrente, temp_mandata_legacy, COP_legacy, temp_mandata_legacy - temp_interna_setpoint)
		conta += 1

COP_totale_legacy /= gradi_mandata_legacy
COP_totale_smart /= gradi_mandata_smart

print "SMART CONTROL    => Total Inflow - Internal Setpoint Temperature {0:4.1f} C".format(gradi_mandata_smart)
print "SMART CONTROL    => Total Inflow - COP {0:4.1f}".format(COP_totale_smart)
print "LEGACY CONTROL   => Total Inflow - Internal Setpoint Temperature {0:4.1f} C".format(gradi_mandata_legacy)
print "LEGACY CONTROL   => Total Inflow - COP {0:4.1f}".format(COP_totale_legacy)
f.close()
