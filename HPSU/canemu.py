#!/usr/bin/env python
# -*- coding: utf-8 -*-
# v 0.0.1 by Vanni Brutto (Zanac)
import sys

class CanEMU(object):
    hspu = None
    def __init__(self, hpsu=None):
        self.hpsu = hpsu
        
    def eprint(self, *args):
        sys.stderr.write(' '.join(map(str,args)) + '\n')
    
    def sendCommandWithID(self, cmd):
        arrResponse = [
            {"name":"t_hs","resp":"32 10 FA 01 D6 01 0C"},
            {"name":"t_hs_set","resp":"32 10 02 01 01 00 00"},
            {"name":"water_pressure","resp":"32 10 FA C0 B4 00 22"},
            {"name":"t_ext","resp":"62 10 FA 0A 0C ff 69"},
            {"name":"t_dhw","resp":"32 10 0E 01 B1 00 00"},
            {"name":"t_dhw_set","resp":"32 10 03 01 CC 00 00"},
            {"name":"t_return","resp":"32 10 16 00 DF 00 00"},
            {"name":"flow_rate","resp":"32 10 FA 01 DA 05 70"},
            {"name":"t_hc","resp":"22 0A 0F 00 EB 00 00"},
            {"name":"t_hc_set","resp":"62 10 04 01 01 00 00"},
            {"name":"status_pump","resp":"32 10 FA 0A 8C 00 01"},
            {"name":"runtime_comp","resp":"32 10 FA 06 A5 01 98"},
            {"name":"runtime_pump","resp":"32 10 FA 06 A4 02 36"},
            {"name":"posmix","resp":"32 10 FA 06 9B 00 00"},
            {"name":"qboh","resp":"32 10 FA 09 1C 00 18"},
            {"name":"qchhp","resp":"32 10 FA 09 20 00 04"},
            {"name":"qsc","resp":"32 10 FA 06 A6 00 00"},
            {"name":"qch","resp":"32 10 FA 06 A7 08 AF"},
            {"name":"qwp","resp":"32 10 FA 09 30 0A 13"},
            {"name":"qdhw","resp":"32 10 FA 09 2C 01 7B"},
            {"name":"sw_vers_01","resp":"32 10 FA 01 99 01 6E"},
            {"name":"sw_vers_02","resp":"32 10 FA C0 B4 00 22"},
            {"name":"sw_vers_03","resp":"32 10 FA 02 4B 20 41"},
            {"name":"mode_01","resp":"32 10 FA 01 12 03 00"},
            {"name":"tvbh2","resp":"22 0A FA C1 02 01 3B"},
            {"name":"tliq2","resp":"22 0A FA C1 03 01 36"},
            {"name":"tr2","resp":"22 0A FA C1 04 00 FA"},
            {"name":"ta2","resp":"22 0A FA C1 05 ff 4B"},
            {"name":"tdhw2","resp":"22 0A FA C1 06 01 C3"},
            {"name":"quiet","resp":"22 0A FA C1 07 00 00"},
            {"name":"mode","resp":"22 0A FA C0 F6 00 01"},
            {"name":"pump","resp":"22 0A FA C0 F7 00 4C"},
            {"name":"ext","resp":"22 0A FA C0 F8 00 00"},
            {"name":"ehs","resp":"22 0A FA C0 F9 00 00"},
            {"name":"rt","resp":"22 0A FA C0 FA 00 01"},
            {"name":"bpv","resp":"22 0A FA C0 FB 00 00"}]

        if cmd["name"] == "runtime_pump":
            #self.eprint("Error sending %s" % (cmd["name"]))
            self.hpsu.printd('warning', 'sending cmd %s (rc:%s)' % (cmd["name"], "ko"))
            return "KO"
        
        for r in arrResponse:
            if r["name"] == cmd["name"]:
                return r["resp"]

        return "KO"
