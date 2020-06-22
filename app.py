import io
from flask import Flask, render_template
import pandas as pd
import gmaps


app = Flask(__name__)
apiKey = 'apiKey'
GoogleMaps(app, key=apiKey)
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
            if (x[arg]) == 0 or x[arg] == "NaN":

                colors.append('rgba(171,243,0, 0.7)')
            elif (x[arg]) < 25 and (x[arg] ) > 0:

                colors.append('rgba(252,255,0, 0.9)')
            elif (x[arg]) < 50 and (x[arg]) > 25:

                colors.append('rgba(255,189,0, 0.7)')
            elif (x[arg]) < 75 and (x[arg]) > 50:

                colors.append('rgba(255,119,0, 0.8)')
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

    # add changes
    states = ['North Carolina','North Dakota','Alabama','Alaska','Arizona','Arkansas',
            'California','Colorado','Connecticut','Delaware','Florida','Georgia',
            'Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Wyoming',
            'Wisconsin','West Virginia','Washington','Virginia','Vermont','Utah',
            'Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina',
            'South Dakota','Tennessee','Texas','New York','New Jersey','Mississippi',
            'Louisiana','Kentucky','Maine','Maryland','Massachusetts','Michigan',
            'Minnesota','Missouri','Montana','Nebraska','Nevada','New Mexico']
    newdfLis = addChanges(states,val,dfList)

    #create geospatial array
    stateArr = createGeoSpatial(newdfLis)

    #set colors
    sizes = size_states(stateArr,'blackPop%')
    sizesT = size_states(stateArr,'Avg Time spent home')
    sizesA = size_states(stateArr,'asianPop%')
    sizesH = size_states(stateArr,'hispanicPop%')
    sizesNA = size_states(stateArr,'NativeAmericanPop%')
    sizesD = size_states(stateArr,'confirmed_deaths')
    sizesC = size_states(stateArr,'confirmed_cases')

    colors = setColorArgs(stateArr,'% change in cases')
    colorsD = setColorArgs(stateArr,'% change in deaths')
#     mapFigure = createMap(stateArr, (40.75, -74.00),colors,'blackPop%')


    return render_template('index.html', stateArr = stateArr,length = len(stateArr), colors = colors,sizes = sizes,sizesH = sizesH,sizesT = sizesT,sizesA = sizesA,sizesD = sizesD,sizesC = sizesC,sizesNA = sizesNA,colorsD = colorsD)



if __name__ == '__main__':
    app.run_server()
# app.run(host='0.0.0.0', port=5000, debug=True)
