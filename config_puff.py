#BASE CONFIG
NUM_PERIODS = 24 # Number of periods in Restart output cycle (NRESPD)
#MRESTART = 3 # SISTEMALO; ORA LO IGNORA
IOUTU = 2 # conc_dep: 1=g/m3_g/m2/s(mass), 2=odour_-(odour), 3=Bq/m3_Bq/m2/s(radiation) # unit� misura output 
IPRTU = 5 # conc_dep: 1=g/m3_g/m2/s, 2=mg/m3_mg/m2/s, 3=ug/m3_ug/m2/s, 4=ng/m3_ng/m2/s, 5=odor_-, 6=TBq/m3_TBq/m2/s, 7=GBq/m3_GBq/m2/s, Bq/m3_Bq/m2/s # unit� misura output
NSFTAB = 2  # Number of scaling factors - CAMBIARE FALLA AUTOMATICAMENTE

# *************************************************************************************
#SPECIES CONFIG - dry_deposition: 1=gas, 2=part
SPECIES = {
    "VOC": {"dry_deposition": 1, 
            "gas_inq": {"diffus" :"0.1345", "alfa" : "1.0", "react" : "2.0", "Mesophyll" : "25.0", "Henry_coef" : "18.0"}, 
            "dry_inq": None, 
            "wet_inq": {"Liq_Prec" : "3.0E-05", "Froz_Prec" : "0.0E00"}} 
}
#NSPEC = 0 Number of species in the model (NSPEC)
#NSE = 0 Number of species in the emitted
#[cspec_temp]
#[mod_string_temp]
#[save_string_temp] 
#[gas_string_temp]
#[dry_string_temp]
#[wet_string_temp]

# *************************************************************************************
#PUNTUAL EMISSION
NPT1 = 4 # num of source in the .inp file
IPTU = 5  # units of emission rate: 1=g/s, 2=kg/h, 3=lb/h, 4=Tons/y, 5=odor*m3/s, 6=odor*m3/min, 7=metric tons/y, 8=Bq/s, 9=GBq/y
POINT_NAMES = ['DUMMY.DAT']  # [is_point] [POINT_NAME] NPTDAT
NPT2 = 0  # num of source from external file if > 0 ignore NPT1 and IPTU
Puntual_Emission = [{    
    "source_name": "E3_1",
    "coord_x": 652.736,
    "coord_y": 5009.459,
    "height": 20.0,
    "base_elev": 27.0,
    "diam": 2.20,
    "vel": 9.93,
    "temp": 293.0,
    "flag_bldg": 0,
    "emis_rates": [5.47E+04]},
    
    {"source_name": "E4_1",
    "coord_x": 652.793,
    "coord_y": 5009.458,
    "height": 16.0,
    "base_elev": 26.0,
    "diam": 1.10,
    "vel": 12.03,
    "temp": 293.0,
    "flag_bldg": 0,
    "emis_rates": [2.07E+03]},
    
    {"source_name": "E3_2",
    "coord_x": 652.736,
    "coord_y": 5009.459,
    "height": 20.0,
    "base_elev": 27.0,
    "diam": 2.20,
    "vel": 9.93,
    "temp": 293.0,
    "flag_bldg": 0,
    "emis_rates": [5.47E+04]},
    
    {"source_name": "E4_2",
    "coord_x": 652.793,
    "coord_y": 5009.458,
    "height": 16.0,
    "base_elev": 26.0,
    "diam": 1.10,
    "vel": 12.03,
    "temp": 293.0,
    "flag_bldg": 0,
    "emis_rates": [2.07E+03]}]

# non considero per emissioni costanti
scal_fact_punt_sor = [{"source_name": "E3_1",
                        "pollutant": "VOC",
                        "scaling_factor": "POINTS_DIURNAL_1"},
                        {"source_name": "E4_1",
                        "pollutant": "VOC",
                        "scaling_factor": "POINTS_DIURNAL_1"},
                        {"source_name": "E3_2",
                        "pollutant": "VOC",
                        "scaling_factor": "POINTS_DIURNAL_2"},
                        {"source_name": "E4_2",
                        "pollutant": "VOC",
                        "scaling_factor": "POINTS_DIURNAL_2"}]
#NSPT1 calcolato

# *************************************************************************************
#Area Emission
NAR1 = 0 # num of source in the .inp file
IARU = 5  # units of emission rate: 1=g/m2s, 2=kg/m2h, 3=lb/m2h, 4=Tons/m2y, 5=odor*m3/m2s, 6=odor*m3/m2min, 7=metric tons/m2y, 8=Bq/m2s, 9=GBq/m2y
AREA_NAMES = ['DUMMY.DAT'] # [is_area] [AREA_NAME] NARDAT EMI_AREALI_YEAR_2024_MONTH_01_12.DAT
NAR2 = 0  # num of source from external file if > 0 ignore NAR1 and IARU
Area_Emission = [{
    "source_name": "A1",
    "height": 40.0,
    "base_elev": 27.0,
    "initial_sigma_z": 0.0,
    "emis_rates": [8.25E00],
    "poligon": [[652.7,5009.508],[652.722,5009.506],[652.723,5009.518],[652.701,5009.52]]},
    
    {"source_name": "A2",
    "height": 40.0,
    "base_elev": 27.0,
    "initial_sigma_z": 0.0,
    "emis_rates": [8.25E00],
    "poligon": [[652.699,5009.495],[652.721,5009.493],[652.723,5009.506],[652.7,5009.508]]},
    
    {"source_name": "A3",
    "height": 40.0,
    "base_elev": 26.0,
    "initial_sigma_z": 0.0,
    "emis_rates": [8.25E00],
    "poligon": [[652.698,5009.479],[652.72,5009.478],[652.721,5009.492],[652.699,5009.493]]},
    
    {"source_name": "A4",
    "height": 40.0,
    "base_elev": 26.0,
    "initial_sigma_z": 0.0,
    "emis_rates": [8.25E00],
    "poligon": [[652.697,5009.47],[652.72,5009.468],[652.72,5009.477],[652.698,5009.479]]}]

scal_fact_area_sor = []
 #[{"source_name": "Area1",
  #                      "pollutant": "NOX",
   #                     "scaling_factor": "POINTS_DIURNAL"},
    #                    {"source_name": "Area1",
     #                   "pollutant": "PM10",
      #                  "scaling_factor": "POINTS_DIURNAL"}]
#NSAR1 calcolato

# *************************************************************************************
#Volume Emission
NVL1 = 0 # num of source in the .inp file
IVLU = 1  # units of emission rate: 1=g/s, 2=kg/h, 3=lb/h, 4=Tons/y, 5=odor*m3/s, 6=odor*m3/min, 7=metric tons/y, 8=Bq/s, 9=GBq/y
VOLUME_NAMES = ['DUMMY.DAT'] # [is_volume] [VOLUME_NAME] NVOLDAT
NVL2 = 0  # num of source from external file if > 0 ignore NVL1 and IVLU
Volume_Emission = [{
    "source_name": "Volume1",
    "height": 9.0,
    "base_elev": 0.0,
    "position" : [474.124, 4945.722],
    "initial_sigma_z": 7,
    "initial_sigma_y": 10,
    "emis_rates": [2.00E-002, 3.00E-002]},
    {"source_name": "Volume2",
    "height": 9.0,
    "base_elev": 0.0,
    "position" : [474.122, 4945.720],
    "initial_sigma_z": 7,
    "initial_sigma_y": 10,
    "emis_rates": [2.00E-002, 3.00E-002]}]

scal_fact_vol_sor = []
#NSVL1 calcolato


# *************************************************************************************
#Flare Emission
NFL2  = 0 # num of source from external file, non ci sono altri parametri
FLARE_NAMES = ['DUMMY.DAT'] # [is_flare] [FLARE_NAME] NFLDAT


# *************************************************************************************
#Road Emission
NRD1 = 0 # num of source in the .inp file
IRDU = 1  # units of emission rate
ROAD_NAMES = ['DUMMY.DAT'] # [is_road] [ROAD_NAME] NRDDAT
NRD2 = 0  # num of source from external file if > 0 ignore NRD1 and IRDU
Road_Emission = [{
    "source_name": "Road1",
    "Effect_height": 9.0,
    "position_xyz" : [[330, 4850, 0.000],[332, 4848, 0.000],[335, 4842, 0.000]], # calcolato NPTROAD
    "initial_sigma_z": 7,
    "initial_sigma_y": 10,
    "emis_rates": [2.00E-002, 3.00E-002]},
    {"source_name": "Road2",
    "Effect_height": 9.0,
    "position_xyz" : [[331, 4850, 0.000],[333, 4848, 0.000],[336, 4842, 0.000]], # calcolato NPTROAD
    "initial_sigma_z": 7,
    "initial_sigma_y": 10,
    "emis_rates": [2.00E-002, 3.00E-002]}]

scal_fact_road_sor = []
#NSFRDS calcolato

# *************************************************************************************
#Boyant Line Emission
NLN2 = 0 # num of source from external file if > 0 ignore il resto
NLINES = 0  # num of source in the .inp file
ILNU = 1  # units of emission rate
LINE_NAMES = ['DUMMY.DAT'] # [is_line] [LINE_NAME] NLNDAT
MXNSEG = 2  # max number of segments
# se NLN2 == 0 e NLINES > 0
NLRISE = 1  # num of rise points
XL = 20 # lunghezza media edifici 
HBL = 30 # altezza media edifici 
WBL = 20 # larghezza media edifici 
DXL = 10# separazione media edifici 
FPRIMEL = 10000 # buoyancy media ????
WML = 10 # larghezza media source line


Line_Emission = [{
    "source_name": "Line1",
    "position_xy" : [[330, 4850],[332, 4848]],
    "relase_height": 9.0,
    "base_elev": 0.0,
    "emis_rates": [2.00E-002, 3.00E-002]},
    {"source_name": "Line2",
    "position_xy" : [[331, 4850],[333, 4848]],
    "relase_height": 9.0,
    "base_elev": 0.0,
    "emis_rates": [2.00E-002, 3.00E-002]}]

scal_fact_line_sor = []
#NSLN1 calcolato

# *************************************************************************************
#SCALING FACTORS
TABELLA = True
#"HOUR24_DAY7" 'CONSTANT1', 'MONTH12', 'DAY7', 'HOUR24', 'HOUR24_DAY7', 'HOUR24_MONTH12', 'WSP6', 'WSP6_PGCLASS6', 'TEMPERATURE12'
TABELLA_FINALE_HD = [{'index' : "1", 'factor_name' : "POINTS_DIURNAL_1", 'factor_type' : 'HOUR24_DAY7'},
                     {'index' : "2", 'factor_name' : "POINTS_DIURNAL_2", 'factor_type' : 'HOUR24_DAY7'}]
TABELLA_FINALE_MONTH12 = {"1" : [1,1,1,1,1,1,1,1,1,1,1,1]} # parte da gennaio
TABELLA_FINALE_HOUR24 = {"1" : [0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0],  # Ora 1 = 00:00–01:00
                         "2" : [0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0]}  # 
TABELLA_FINALE_DAY7 = {"1" : [1,1,1,1,1,0,0],
                       "2" : [0,0,0,0,0,1,0]} # parte da lunedì