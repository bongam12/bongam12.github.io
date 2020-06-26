import io
from flask import Flask, render_template
from flask_caching import Cache
import pandas as pd
import gmaps


cache = Cache(config={'CACHE_TYPE': 'simple'})

app = Flask(__name__)
cache.init_app(app)


def loadData(ls):
    dfList = []
    for x in ls:
        dfList.append(pd.read_csv('data/'+x))
    return dfList


def addChanges(states,changed,dfList):
    newdfLis = []
    for x in range(len(dfList)):
#         ls = dfList[x].countyName.unique()
        changedN = changed.loc[changed['Province_State'] == states[x]]

        joinPd1 = dfList[x].merge(changedN, left_on='Admin2', right_on='Admin2')
        newdfLis.append(joinPd1)
    return newdfLis


def createGeoSpatial(ls):
    stateArr = []
    for x in ls:
        for index, row in x.iterrows():

            #print(row['countyName'], row['Lat'], row['Long_'])
            stateArr.append({'HawaiianPop%':(row['NA_MALE']+row['NA_FEMALE'])/row['TOT_POP'] *100,'NativeAmericanPop%':(row['IA_MALE']+row['IA_FEMALE'])/row['TOT_POP']*100,'asianPop%':(row['AA_MALE']+row['AA_FEMALE'])/row['TOT_POP']*100,'hispanicPop%':(row['H_MALE']+row['H_FEMALE'])/row['TOT_POP']*100,'whitePop%':(row['WA_MALE']+row['WA_FEMALE'])/row['TOT_POP']*100,'blackPop%':(row['BA_MALE']+row['BA_FEMALE'])/row['TOT_POP']*100,'% change in deaths': row['% change in deaths'],'Current Deaths':row['Current_Deaths'],'name': row['countyName'], 'location': (row['Lat'], row['Long_']),'lat': row['Lat'],'long':  row['Long_'],'% change in cases':(round(row['% change in cases'],2) * 100),'Qty change in cases':int(round(row['change in cases'])), 'confirmed_cases': int(round(row['Current_Confirmed'])), 'confirmed_deaths': int(round(row['Deaths'])),'distance_traveled_from_home':int(round(row['distance_traveled_from_home'])),'Black or African American alone male population':int(round(row['BA_MALE'])),'White alone male population':int(round(row['WA_MALE'])),'Avg Time spent home':round(int(round(row['median_home_dwell_time']))/60)})
    return stateArr



def setColorArgs(states,arg):
    colors = []
    for x in states:
        if arg == '% change in cases' or arg == '% change in deaths':
            if (x[arg]) < 0:

                colors.append('rgba(155,212,228, 0.7)')
            elif (x[arg]) == 0 or x[arg] == "NaN":

                colors.append('rgba(171,243,0, 0.7)')
            elif (x[arg]) < 33 and (x[arg] ) > 0:

                colors.append('rgba(252,255,0, 0.9)')
            elif (x[arg]) < 66 and (x[arg]) > 33:

                colors.append('rgba(255,189,0, 0.7)')
            elif (x[arg]) < 99 and (x[arg]) > 66:

                colors.append('rgba(255,119,0, 0.8)')
            elif (x[arg]) > 99:

                colors.append('rgba(73,0,0, 0.8)')
            else:
                colors.append('rgba(200, 0, 0, 0.9)')

        else:

            if int(x[arg] * .02) == 0:

                colors.append('rgba(0,0,255, 0.7)')
            elif int(x[arg] * .02) < 5 and int(x[arg] * .02) > 0:
                   #500 deaths
                colors.append('rgba(255,215,0, 0.9)')
            elif int(x[arg] * .02) < 10 and int(x[arg] * .02) > 5:
                   #500 deaths
                colors.append('rgba(255,92,21, 0.7)')
            else:
                colors.append('rgba(200, 0, 0, 0.7)')
    return colors


def createMap(states,originCoord,colors,arg):
    plant_locations = [plant['location'] for plant in states]
    info_box_template = """
    <dl>
    <dt>Name</dt><dd>{name}</dd>
    <dt>Number of Confirmed Cases</dt><dd>{confirmed_cases}</dd>
    <br>
    <dt>Number of Confirmed Deaths</dt><dd>{confirmed_deaths}</dd>
    <br>
    <dt>Avg time spent at home</dt><dd>{Avg Time spent home} hours</dd>
    <br>
    <dt>Avg distance traveled from home</dt><dd>{distance_traveled_from_home}</dd>
    <br>
    <dt>Hispanic population</dt><dd>{hispanicPop%}</dd>
    <br>
    <dt>Black or African American population</dt><dd>{blackPop%}</dd>
    <br>
    <dt>White  population</dt><dd>{whitePop%}</dd>
    <br>
    <dt>% increase in cases</dt><dd>{% change in cases}%</dd>
    </dl>
    """
    plant_info = [info_box_template.format(**plant) for plant in states]
    marker_layer = gmaps.symbol_layer(plant_locations, info_box_content=plant_info,fill_color=colors,stroke_color=colors)


    count = 0
    for x in states:
        if arg == 'Current Deaths':
            if int(x[arg] * .02) == 0:
                marker_layer.markers[count].scale = 2
            else:
                #over 500 deaths
                marker_layer.markers[count].scale = int(x[arg] * .02)
        elif arg == 'blackPop%' or arg == 'whitePop%' or arg == 'hispanicPop%' or arg == 'asianPop%' or arg == 'NativeAmericanPop%':
            if int(x[arg]/10) < 1:
                marker_layer.markers[count].scale = 2
            else:
                #over 10% deaths
                marker_layer.markers[count].scale = int(x[arg] / 10)
        elif arg == 'Avg Time spent home':
            if int(x[arg]) > 10:
                marker_layer.markers[count].scale = 2
            elif int(x[arg]) < 10 and int(x[arg]) > 6:
                #over 500 deaths
                marker_layer.markers[count].scale = 4
            else:
                marker_layer.markers[count].scale = 6
        else:
            if int(x[arg] * .0007) == 0:
                marker_layer.markers[count].scale = 2
            else:
                marker_layer.markers[count].scale = int(x[arg] * .0007)

        count = count + 1
    figure_layout = {
        'width': '1500px',
        'height': '800px',
        'border': '1px solid black',
        'padding': '1px'
    }
    fig = gmaps.figure(center=originCoord, zoom_level=8,layout=figure_layout)

    fig.add_layer(marker_layer)
    return fig


def size_states(states,arg):

    sizes = []
    for x in states:
        if arg == 'confirmed_deaths':
            if int(x[arg] * .02) == 0:
                sizes.append(2)
            else:
                #over 200 deaths
                sizes.append(int(x[arg] * .02))
        elif arg == 'confirmed_cases':
            if int(x[arg] * .001) == 0:
                sizes.append(2)
            else:
                #over 1000 deaths
                sizes.append(int(x[arg] * .001))

        elif arg == 'asianPop%':
            if int(x[arg]/2) < 1:
                sizes.append(2)
            else:

                sizes.append(int(x[arg] / 2))
        elif arg == 'NativeAmericanPop%':
            if int(x[arg]/5) < 1:
                sizes.append(2)
            else:

                sizes.append(int(x[arg] / 5))

        elif arg == 'blackPop%' or arg == 'whitePop%' or arg == 'hispanicPop%' :
            if int(x[arg]/10) < 1:
                sizes.append(2)
            else:

                sizes.append(int(x[arg] / 10))
        elif arg == 'Avg Time spent home':
            if int(x[arg]) > 10:
                sizes.append(2)
            elif int(x[arg]) < 10 and int(x[arg]) > 6:

                sizes.append(40/int(x[arg]))
            else:
                if int(x[arg]) == 0:  
                    sizes.append(25)
                else:
                    sizes.append(50/int(x[arg]))
        else:
            if int(x[arg] * .0007) == 0:
                sizes.append(2)
            else:
                sizes.append(int(x[arg] * .0007))


    return sizes
@app.route("/")
def home():
    gmaps.configure(api_key='AIzaSyBoscrKoGi4KLRAbAyXrx8hYsDzcuoWCcs')

    dataList = ['NorthCarolinaApril.csv','NorthDakotaApril.csv','AlabamaApril.csv','AlaskaApril.csv','ArizonaApril.csv','ArkansasApril.csv',
            'CaliforniaApril.csv','ColoradoApril.csv','ConnecticutApril.csv','DelawareApril.csv','FloridaApril.csv','GeorgiaApril.csv',
            'HawaiiApril.csv','IdahoApril.csv','IllinoisApril.csv','IndianaApril.csv','IowaApril.csv','KansasApril.csv','WyomingApril.csv',
            'WisconsinApril.csv','WestVirginiaApril.csv','WashingtonApril.csv','VirginiaApril.csv','VermontApril.csv','UtahApril.csv',
            'OhioApril.csv','OklahomaApril.csv','OregonApril.csv','PennsylvaniaApril.csv','RhodeIslandApril.csv','SouthCarolinaApril.csv',
            'SouthDakotaApril.csv','TennesseeApril.csv','TexasApril.csv','New YorkApril.csv','New JerseyApril.csv','MississippiApril.csv',
            'LouisianaApril.csv','KentuckyApril.csv','MaineApril.csv','MarylandApril.csv','MassachusettsApril.csv','MichiganApril.csv',
            'MinnesotaApril.csv','MissouriApril.csv','MontanaApril.csv','NebraskaApril.csv','NevadaApril.csv','New MexicoApril.csv']
    
    dataList2 = ['North CarolinaMay.csv','North DakotaMay.csv','AlabamaMay.csv','AlaskaMay.csv','ArizonaMay.csv','ArkansasMay.csv',
            'CaliforniaMay.csv','ColoradoMay.csv','ConnecticutMay.csv','DelawareMay.csv','FloridaMay.csv','GeorgiaMay.csv',
            'HawaiiMay.csv','IdahoMay.csv','IllinoisMay.csv','IndianaMay.csv','IowaMay.csv','KansasMay.csv','WyomingMay.csv',
            'WisconsinMay.csv','West VirginiaMay.csv','WashingtonMay.csv','VirginiaMay.csv','VermontMay.csv','UtahMay.csv',
            'OhioMay.csv','OklahomaMay.csv','OregonMay.csv','PennsylvaniaMay.csv','Rhode IslandMay.csv','South CarolinaMay.csv',
            'South DakotaMay.csv','TennesseeMay.csv','TexasMay.csv','New YorkMay.csv','New JerseyMay.csv','MississippiMay.csv',
            'LouisianaMay.csv','KentuckyMay.csv','MaineMay.csv','MarylandMay.csv','MassachusettsMay.csv','MichiganMay.csv',
            'MinnesotaMay.csv','MissouriMay.csv','MontanaMay.csv','NebraskaMay.csv','NevadaMay.csv','New MexicoMay.csv']
    
  
    
    dataList4 = ['North CarolinaJune.csv','North DakotaJune.csv','AlabamaJune.csv','AlaskaJune.csv','ArizonaJune.csv','ArkansasJune.csv',
            'CaliforniaJune.csv','ColoradoJune.csv','ConnecticutJune.csv','DelawareJune.csv','FloridaJune.csv','GeorgiaJune.csv',
            'HawaiiJune.csv','IdahoJune.csv','IllinoisJune.csv','IndianaJune.csv','IowaJune.csv','KansasJune.csv','WyomingJune.csv',
            'WisconsinJune.csv','West VirginiaJune.csv','WashingtonJune.csv','VirginiaJune.csv','VermontJune.csv','UtahJune.csv',
            'OhioJune.csv','OklahomaJune.csv','OregonJune.csv','PennsylvaniaJune.csv','Rhode IslandJune.csv','South CarolinaJune.csv',
            'South DakotaJune.csv','TennesseeJune.csv','TexasJune.csv','New YorkJune.csv','New JerseyJune.csv','MississippiJune.csv',
            'LouisianaJune.csv','KentuckyJune.csv','MaineJune.csv','MarylandJune.csv','MassachusettsJune.csv','MichiganJune.csv',
            'MinnesotaJune.csv','MissouriJune.csv','MontanaJune.csv','NebraskaJune.csv','NevadaJune.csv','New MexicoJune.csv']
    
    
   
    
    dfList4 = cache.get('dfList4')
    if dfList4 == None:
        dfList4 = loadData(dataList4)
        cache.set('dfList2', dfList4)
   

    states = ['North Carolina','North Dakota','Alabama','Alaska','Arizona','Arkansas',
            'California','Colorado','Connecticut','Delaware','Florida','Georgia',
            'Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Wyoming',
            'Wisconsin','West Virginia','Washington','Virginia','Vermont','Utah',
            'Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina',
            'South Dakota','Tennessee','Texas','New York','New Jersey','Mississippi',
            'Louisiana','Kentucky','Maine','Maryland','Massachusetts','Michigan',
            'Minnesota','Missouri','Montana','Nebraska','Nevada','New Mexico']
    
    stateArr = cache.get('stateArr')
    sizes = cache.get('sizes')
    sizesT =cache.get('sizesT')
    sizesA = cache.get('sizesA')
    sizesH = cache.get('sizesH')
    sizesNA = cache.get('sizesNA')
    sizesD = cache.get('sizesD')
    sizesC = cache.get('sizesC')
    colors = cache.get('colors')
    colorsD = cache.get('colorsD')
    if stateArr == None:
        dfList = loadData(dataList)
        
        changePerc = pd.read_csv('data/change%list.csv')
        changePerc['change in cases'] = changePerc['change in cases'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc['% change in cases'] = changePerc['% change in cases'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc['Current_Confirmed'] = changePerc['Current_Confirmed'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc['% change in deaths'] = changePerc['% change in deaths'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc['Current_Deaths'] = changePerc['Current_Deaths'].map(lambda x: x.lstrip('[').rstrip(']'))
        
        
        val = changePerc.replace('', 0)
        #alter Val formating
        val['change in cases'] = (val['change in cases'].astype('int'))
        val['% change in cases'] = (val['% change in cases'].astype('float'))
        val['Current_Confirmed'] = (val['Current_Confirmed'].astype('int'))
        val['% change in deaths'] = (val['% change in deaths'].astype('float'))
        val['Current_Deaths'] = (val['Current_Deaths'].astype('int'))
        
        newdfLis = addChanges(states,val,dfList)
        
        stateArr = createGeoSpatial(newdfLis)
        
        #set colors - April
        sizes = size_states(stateArr,'blackPop%')
        sizesT = size_states(stateArr,'Avg Time spent home')
        sizesA = size_states(stateArr,'asianPop%')
        sizesH = size_states(stateArr,'hispanicPop%')
        sizesNA = size_states(stateArr,'NativeAmericanPop%')
        sizesD = size_states(stateArr,'confirmed_deaths')
        sizesC = size_states(stateArr,'confirmed_cases')

        colors = setColorArgs(stateArr,'% change in cases')
        colorsD = setColorArgs(stateArr,'% change in deaths')
        
        
        
        #cache information
        cache.set('stateArr', stateArr)
        cache.set('sizes', sizes)
        cache.set('sizesT', sizesT)
        cache.set('sizesA', sizesA)
        cache.set('sizesH', sizesH)
        cache.set('sizesNA', sizesNA)
        cache.set('sizesD', sizesD)
        cache.set('sizesC', sizesC)
        cache.set('colors', colors)
        cache.set('colorsD', colorsD)
        
    #second state array for may
    stateArr2 = cache.get('stateArr2')
    sizes2 = cache.get('sizes2')
    sizesT2 =cache.get('sizesT2')
    sizesA2 = cache.get('sizesA2')
    sizesH2 = cache.get('sizesH2')
    sizesNA2 = cache.get('sizesNA2')
    sizesD2 = cache.get('sizesD2')
    sizesC2 = cache.get('sizesC2')
    colors2 = cache.get('colors2')
    colorsD2 = cache.get('colorsD2')
    if stateArr2 == None:
        dfList2 = loadData(dataList2)
        
        changePerc2 = pd.read_csv('data/change%listMay.csv')
        changePerc2['change in cases'] = changePerc2['change in cases'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc2['% change in cases'] = changePerc2['% change in cases'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc2['Current_Confirmed'] = changePerc2['Current_Confirmed'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc2['% change in deaths'] = changePerc2['% change in deaths'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc2['Current_Deaths'] = changePerc2['Current_Deaths'].map(lambda x: x.lstrip('[').rstrip(']'))
        
        
        val2 = changePerc2.replace('', 0)
        val2['change in cases'] = (val2['change in cases'].astype('int'))
        val2['% change in cases'] = (val2['% change in cases'].astype('float'))
        val2['Current_Confirmed'] = (val2['Current_Confirmed'].astype('int'))
        val2['% change in deaths'] = (val2['% change in deaths'].astype('float'))
        val2['Current_Deaths'] = (val2['Current_Deaths'].astype('int'))
        
        newdfLis2 = addChanges(states,val2,dfList2)
        
        stateArr2 = createGeoSpatial(newdfLis2)
        
        #set colors - May
        sizes2 = size_states(stateArr2,'blackPop%')
        sizesT2 = size_states(stateArr2,'Avg Time spent home')
        sizesA2 = size_states(stateArr2,'asianPop%')
        sizesH2 = size_states(stateArr2,'hispanicPop%')
        sizesNA2 = size_states(stateArr2,'NativeAmericanPop%')
        sizesD2 = size_states(stateArr2,'confirmed_deaths')
        sizesC2 = size_states(stateArr2,'confirmed_cases')

        colors2 = setColorArgs(stateArr2,'% change in cases')
        colorsD2 = setColorArgs(stateArr2,'% change in deaths')
        
        
        
        #cache information
        cache.set('stateArr2', stateArr2)
        cache.set('sizes2', sizes2)
        cache.set('sizesT2', sizesT2)
        cache.set('sizesA2', sizesA2)
        cache.set('sizesH2', sizesH2)
        cache.set('sizesNA2', sizesNA2)
        cache.set('sizesD2', sizesD2)
        cache.set('sizesC2', sizesC2)
        cache.set('colors2', colors2)
        cache.set('colorsD2', colorsD2)
        
        
    #third state array for june
    stateArr4= cache.get('stateArr4')
    sizes4 = cache.get('sizes4')
    sizesT4 =cache.get('sizesT4')
    sizesA4 = cache.get('sizesA4')
    sizesH4 = cache.get('sizesH4')
    sizesNA4 = cache.get('sizesNA4')
    sizesD4 = cache.get('sizesD4')
    sizesC4 = cache.get('sizesC4')
    colors4 = cache.get('colors4')
    colorsD4 = cache.get('colorsD4')
    if stateArr4 == None:
        dfList4 = loadData(dataList4)
        
        changePerc4 = pd.read_csv('data/change%listJune.csv')
        changePerc4['change in cases'] = changePerc4['change in cases'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc4['% change in cases'] = changePerc4['% change in cases'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc4['Current_Confirmed'] = changePerc4['Current_Confirmed'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc4['% change in deaths'] = changePerc4['% change in deaths'].map(lambda x: x.lstrip('[').rstrip(']'))
        changePerc4['Current_Deaths'] = changePerc4['Current_Deaths'].map(lambda x: x.lstrip('[').rstrip(']'))
        
        
        val4 = changePerc4.replace('', 0)
        val4['change in cases'] = (val4['change in cases'].astype('int'))
        val4['% change in cases'] = (val4['% change in cases'].astype('float'))
        val4['Current_Confirmed'] = (val4['Current_Confirmed'].astype('int'))
        val4['% change in deaths'] = (val4['% change in deaths'].astype('float'))
        val4['Current_Deaths'] = (val4['Current_Deaths'].astype('int'))
        
        newdfLis4 = addChanges(states,val4,dfList4)
        
        stateArr4 = createGeoSpatial(newdfLis4)
        
         #set colors - June week 2
        sizes4 = size_states(stateArr4,'blackPop%')
        sizesT4 = size_states(stateArr4,'Avg Time spent home')
        sizesA4 = size_states(stateArr4,'asianPop%')
        sizesH4 = size_states(stateArr4,'hispanicPop%')
        sizesNA4 = size_states(stateArr4,'NativeAmericanPop%')
        sizesD4 = size_states(stateArr4,'confirmed_deaths')
        sizesC4 = size_states(stateArr4,'confirmed_cases')

        colors4 = setColorArgs(stateArr4,'% change in cases')
        colorsD4 = setColorArgs(stateArr4,'% change in deaths')
        
        
        
        #cache information
        cache.set('stateArr4', stateArr4)
        cache.set('sizes4', sizes4)
        cache.set('sizesT4', sizesT4)
        cache.set('sizesA4', sizesA4)
        cache.set('sizesH4', sizesH4)
        cache.set('sizesNA4', sizesNA4)
        cache.set('sizesD4', sizesD4)
        cache.set('sizesC4', sizesC4)
        cache.set('colors4', colors4)
        cache.set('colorsD4', colorsD4)
    
 
    return render_template('index.html', stateArrA = stateArr,lengthA = len(stateArr), colorsA = colors,sizesA = sizes,sizesHA = sizesH,sizesTA = sizesT,sizesAA = sizesA,sizesDA = sizesD,sizesCA = sizesC,sizesNAA = sizesNA,colorsDA = colorsD, stateArrM = stateArr2,lengthM = len(stateArr2), colorsM = colors2,sizesM = sizes2,sizesHM = sizesH2,sizesTM = sizesT2,sizesAM = sizesA2,sizesDM = sizesD2,sizesCM = sizesC2,sizesNAM = sizesNA2,colorsDM = colorsD2,  stateArrJ2 = stateArr4,lengthJ2 = len(stateArr4), colorsJ2 = colors4,sizesJ2 = sizes4,sizesHJ2 = sizesH4,sizesTJ2 = sizesT4,sizesAJ2 = sizesA4,sizesDJ2 = sizesD4,sizesCJ2 = sizesC4,sizesNAJ2 = sizesNA4,colorsDJ2 = colorsD4)

@app.route('/faq')
def stanford_page():
    return render_template('index2.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    
    
    

