from flask import Flask, render_template, request, send_file, session
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
import requests
import pandas
import json
from difflib import get_close_matches
from geopy.geocoders import ArcGIS
import folium
import sys
import glob
from datetime import datetime
import os
from sendEmail import send_email


# dateString = "None"
# locationUpdated = "None"
class SaveValues:
    def __init__(self):
        self.Mainlocation = "None"
        self.dateStringMain = "None"

    def saveVal(self, dateStringMain, Mainlocation, flag):
        if flag == 0:
            self.Mainlocation = Mainlocation
        elif flag == 1:
            self.dateStringMain = dateStringMain
        elif flag == 10:
            self.dateStringMain = dateStringMain
            self.Mainlocation = Mainlocation
        else:
            pass

    def getVal(self):
        return self.dateStringMain, self.Mainlocation

    def getDate(self):
        return self.dateStringMain

    def getLoc(self):
        return self.Mainlocation


sav = SaveValues()


def Findall(place):
    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent':
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
    })

    reqStatus = req = requests.get(
        "https://www.yelp.com/search?find_desc=Restaurants&find_loc={}".format(
            place),
        headers=headers).status_code
    print(reqStatus)
    if reqStatus == 200:
        pass
    else:
        return "fail"

    req = requests.get(
        "https://www.yelp.com/search?find_desc=Restaurants&find_loc={}".format(
            place),
        headers=headers)
    content = req.content

    soup = BeautifulSoup(content, "html.parser")

    List = soup.find_all(
        "div", {
            "class":
            "lemon--div__373c0__1mboc largerScrollablePhotos__373c0__3FEIJ arrange__373c0__UHqhV border-color--default__373c0__2oFDT"
        })

    try:
        Pages = soup.find(
            "div", {
                "class":
                "lemon--div__373c0__1mboc u-padding-b2 border-color--default__373c0__2oFDT text-align--center__373c0__1l506"
            }).find("span").text
    except:
        print("Do Not server here yet Try again later! ")
        return "fail"

    try:
        Pages = (int(Pages.text[-3:]))
    except:
        Pages = 1

    Pages = Pages / (Pages / 1.5)

    Pages = round(Pages)
    print(Pages)
    List_of_values = []
    # print(List)

    for Page in range(0, Pages * 30, 30):
        req = requests.get(
            "https://www.yelp.com/search?find_desc=Restaurants&find_loc={}&start={}"
            .format(place, Page),
            headers=headers)
        content = req.content
        soup = BeautifulSoup(content, "html.parser")
        List = soup.find_all(
            "div", {
                "class":
                "lemon--div__373c0__1mboc largerScrollablePhotos__373c0__3FEIJ arrange__373c0__UHqhV border-color--default__373c0__2oFDT"
            })
        i = 0
        for items in List:
            d = {}
            try:
                d["Headings"] = items.find(
                    "h3", {
                        "lemon--h3__373c0__sQmiG heading--h3__373c0__1n4Of alternate__373c0__1uacp"
                    }).find("a").text
            except:
                d["Headings"] = "None"
            try:
                d["Address"] = items.find(
                    "address", {
                        "class": "lemon--address__373c0__2sPac"
                    }).text
            except:
                d["Address"] = "None"

            try:
                d["Phone"] = items.find(
                    "p", {
                        "class":
                        "lemon--p__373c0__3Qnnj text__373c0__2pB8f text-color--normal__373c0__K_MKN text-align--right__373c0__3ARv7"
                    }).text
            except:
                d["Phone"] = "None"

            try:
                d["Ratings"] = items.find(
                    "div", {
                        "class":
                        "lemon--div__373c0__1mboc attribute__373c0__1hPI_ display--inline-block__373c0__2de_K u-space-r1 border-color--default__373c0__2oFDT"
                    }).find("div").get("aria-label")
                i = i + 1

            except:
                d["Ratings"] = "None"

            List_of_values.append(d)

    df = pandas.DataFrame(List_of_values)
    Arc = ArcGIS()
    try:
        df["Address"] = df["Address"] + "," + place
        df["Coordinate"] = df["Address"].apply(Arc.geocode)
        df["Longitude"] = df["Coordinate"].apply(lambda x: x.longitude
                                                 if x != None else "None")
        df["Latitude"] = df["Coordinate"].apply(lambda x: x.latitude
                                                if x != None else "None")
    except:
        return "fail"

    ratingsNum = []

    def Convo(r):
        for x in r:
            try:
                try:
                    ratingsNum.append(float(x[:4]))
                except:
                    ratingsNum.append(float(x[:3]))
            except:
                pass

    ratings = list(df["Ratings"])
    Convo(ratings)

    def ratColor(r):
        r = float(r)
        if r > 4:
            return "green"
        elif 3 < r < 4:
            return "beige"
        else:
            return "red"

    Lati = list(df["Latitude"])
    Longi = list(df["Longitude"])
    Hedi = list(df["Headings"])
    Addi = list(df["Address"])

    map = folium.Map(location=[Lati[0], Longi[0]],
                     zoom_start=15,
                     tiles="Stamen Terrain")

    html = """
                <h5>Name: %s</h5>
                <div>Ratings: %s Stars<div>
                <div>Address: %s<div>
        """

    fgv = folium.FeatureGroup(name="Main")

    for lat, lon, tit, rating, add in zip(Lati, Longi, Hedi, ratingsNum, Addi):
        iframe = folium.IFrame(html=html % (tit, rating, add),
                               width=200,
                               height=100)
        fgv.add_child(
            folium.Marker(location=[lat, lon],
                          popup=folium.Popup(iframe),
                          icon=folium.Icon(color=ratColor(rating),
                                           icon='info-sign')))

    map.add_child(fgv)
    place = place.lower()
    place = place.replace(" ", "")
    dateString = datetime.today().strftime("%Y-%m-%d")
    # this is when a new Map is created it is called !
    sav.saveVal(dateString, place, 10)
    map.save("static/maps/map-{}-{}.html".format(place, dateString))
    return "pass"


def NeedUpdate(dateString, now):
    NowYear = int(now[:4])
    NowMonth = int(now[5:7])
    NowDays = int(now[8:])
    dateStringYear = int(dateString[:4])
    dateStringMonth = int(dateString[5:7])
    dateStringDays = int(dateString[8:])
    print(NowYear, NowDays, NowMonth)
    print(dateStringDays, dateStringMonth, dateStringYear)
    if NowYear == dateStringYear:
        if NowMonth == dateStringMonth:
            if NowDays - dateStringDays > 15:
                return True
            else:
                return False
        else:
            return True
    else:
        return True


app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'postGRES! <FILL ME !!!!!!!!!!!!!!!>'
app.config['TEMPLATES_AUTO_RELOAD'] = True
# By default the method is get so pass the method as a list !
db = SQLAlchemy(app)


class Data(db.Model):
    __tablename__ = "data"
    id = db.Column(db.Integer, primary_key=True)
    email_ = db.Column(db.String(120))
    place_ = db.Column(db.String(120))

    def __init__(self, email_, place_):
        self.email_ = email_
        self.place_ = place_


@app.route('/')
def home():
    return render_template("Home.html")


@app.route('/Results', methods=['POST'])
def success():
    if request.method == 'POST':
        email = request.form["Email"]
        location = request.form["Place"]
        locationUpdated = location.lower().replace(" ", "")
        print(locationUpdated)
        HitsForPlace = db.session.query(Data).filter(
            Data.place_ == locationUpdated).count()
        find = glob.glob("static/maps/map-{}-*.html".format(locationUpdated))
        print(find, email, location)
        update = False
        try:
            pl = find[0]
            print(pl)
            dateString = pl[-15:-5]
            now = datetime.now().strftime("%Y-%m-%d")
            print(now)
        except:
            update = True

        if update == True or NeedUpdate(dateString, now) == True:
            if find:
                os.remove("static/maps/map-{}-{}.html".format(
                    locationUpdated, dateString))
            string = Findall(location)
        else:
            string = "pass"
            print(dateString, locationUpdated)
            sav.saveVal(dateString, locationUpdated, 10)
            print(sav.getDate(), sav.getLoc())

        if string == "pass":
            data = Data(email, locationUpdated)
            db.session.add(data)
            db.session.commit()
            mapName = "/static/maps/map-{}-{}.html".format(
                sav.getLoc(), sav.getDate())

            send_email(email, HitsForPlace)
            return render_template("Success.html", mapName=mapName)
        else:
            return render_template(
                "Home.html",
                text="Looks Like Something Went Wrong Or We Dont Serve that Location YET!"
            )


@app.route('/about')
def about():
    return render_template("About.html")


if __name__ == "__main__":
    app.run()

# use activate to activate the python in the cmd after creating a virtual environment !
# we are using the sqlAlchemy lib to do all the posgresSql operation since it requires less lines of  code
# to implement some of the psycopg2 offers .. for instance we dont need to commit and close everytime we update the table !x
# db.create_all() method can be used to create the preliminary table !
