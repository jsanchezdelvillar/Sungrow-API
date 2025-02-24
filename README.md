# Sungrow-API
PythonScript files to access Sungrow's iSolarCloud Open API

## Credits

MickMake (https://github.com/MickMake) has a wonderful app named GoSungrow (https://github.com/MickMake/GoSungrow) that creates MQTT sensors in HA for ALL the data points available. It uses a generic AppKey and the user's login information. I have it installed and working without any problems. 

MickMake explicitly says that using the standard API is not the best, but it works, and it's fun to program and debug by yourself. Please be sure to access his repository to see why he finally opted for his solution.

## Why this repository?

While setting up MickMake's app I had some problems with the appkey. So I accesed the 'Applications' menu option from ISolarCloud and was asked to create an app to obtain the appkey. In a couple of days I got my appkey, which didn't work with GoSungrow, and started looking at the API requirements. So, when I finally got GoSungrow working I decided to continue studying this other solution.

## What is it?

It is a DIY way of reading data from a Sungrow installation. You can choose what and when to read it

These files implement the minimum ISolarCloud API calls needed to integrate the data into Home-Assistant.

- A function calls for an update of the sensors.
- If the call fails a function is called to update the token
- An automation runs the first fuction every 5 minutes

## Setup procedure

### Getting the information needed for the API queries

- First you login into ISolarCloud

![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/d148931d3dd7e9440bdbda6e44213b3f15a0e653/images/login.PNG?raw=true)

- Then, when you see the data of your installation, click on the four sqares at the right of the search box

![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/d148931d3dd7e9440bdbda6e44213b3f15a0e653/images/iSolarCloud.PNG)

- In the developer portal you will see a link to the documentation, we will use it later. Click on the link to applications

![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/d148931d3dd7e9440bdbda6e44213b3f15a0e653/images/applications.PNG)

- You will see then a screen where you muct click on 'Create'. In the following image you can see that I already did it, and my request was approved

![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/d148931d3dd7e9440bdbda6e44213b3f15a0e653/images/create.PNG)

  You must give some information about why you need access to the api. In my case I just said I wanted access from Home Assistant, WITHOUT access with OAuth2.0. In a couple of days I entered the screen and the app was approved.

- By clicking in 'Action' 'View' (the first icon below 'Action') you can see all the information you need to call the API

![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/d148931d3dd7e9440bdbda6e44213b3f15a0e653/images/appdata.PNG)

- Finally, you need to obtain your ps_key, a number composed of your ps_id (plant id), number 11 (meaning plant info) and a couple other numbers. You can do this in two ways:
  - Since I had installed GoSungrow, I knew my ps_id (it appears in all the sensors) and then tried with ps-id_11_0_0
  - You can go to the Documentation section and then use the following calls (for each call there is a 'try it' button). Be sure to select V1 (no OAuth2.0):

    ![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/d148931d3dd7e9440bdbda6e44213b3f15a0e653/images/v1.PNG)
    
    [![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/d148931d3dd7e9440bdbda6e44213b3f15a0e653/images/try%20it.PNG)
    
    - Start with the login call:
      
      ![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/f78a856c2c8e6182cc24444a1d396423656931a9/images/login2.PNG)
      
      and you will get a token.
      
      ![alt_text](https://github.com/jsanchezdelvillar/Sungrow-API/blob/f78a856c2c8e6182cc24444a1d396423656931a9/images/token.PNG)
    
    - Then use the Plant List Information Query, then Query Device List and Query Basic Plan Info. Finally you will find the ps_key

### Installation

- Add all needed keys (appkey, secret key, username and password) to **secrets.yaml**
- Add the following line to **configuration.yaml**:
```
pyscript: !include pyscript/config.yaml
```
- Install the integration **Pyscript Python scripting**
- Under Config, create a folder named **pyscript**
- Place in this new folder a new file **config.yaml**
  - Add the following to this file:
```
allow_all_imports: true
hass_is_global: true
  apps:
    Sungrow:
      appkey: !secret sungrow_appkey
      sung_secret: !secret sungrow_secret
      username: !secret sungrow_user
      password: !secret sungrow_password
```
- Create a folder under pyscript called **apps**
- Create a folder under apps called **Sungrow**
- Add the file **__init__.py** with the content of the repository

### Restart Home Assistant

Home Assistant will update all Sensors on startup. In case the token is not valid it will renew it.

## TODO list

Right now it works well enoough for me, and I want to test it before adding additional stuff:

- SECURITY!!! first with RSA encription and then through OAuth2.0
- Adding more sensors from other devices (inverter, meter...)
