# Sungrow-API
Yaml files to access Sungrow's iSolarCloud Open API

## Credits

MickMake (https://github.com/MickMake) has a wonderful app named GoSungrow (https://github.com/MickMake/GoSungrow) that creates MQTT sensors in HA for ALL the data points available. It uses a generic AppKey and the user's login information. I have it installed and working without any problems. 

MickMake explicitly says that using the standard API is not the best, but it works, and it's fun to program and debug by yourself. Please be sure to access his repository to see why he finally opted for his solution.

## Why this repository?

While setting up MickMake's app I had some problems with the appkey. So I accesed the 'Applications' menu option from ISolarCloud and was asked to create an app to obtain the appkey. In a couple of days I got my appkey, which didn't work with GoSungrow, and started looking at the API requirements. So, when I finally got GoSungrow working I decided to continue studying this other solution.

## What is it?

It is a DIY way of reading data from a Sungrow installation. You can choose what and when to read it

These files implement the minimum ISolarCloud API calls needed to integrate the data into Home-Assistant. There are basically three parts:

- A REST Sensor added in configuration.yaml with a login request that gets the token. The token has a life of 24 hours after the last use, so basically it will not expire.
- Also in configuration.yaml, several REST Sensors obtained through a data request, using the token obtained previously. You can easily add more sensors if you need the information.
- Since the information I'm getting does not include the grid power, a template sensor in template.yaml to calculate the difference between the production and the load power.

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

### Modify configuration.yaml and template.yaml

Replace the appkey, the secret key, the ps_key and the point_id list with the values of your plant. You can get a list of all available point_ids in the 'Common Plant Measuring Points' under 'Common Measuring Points Enumeration' in the documentation index.

### Restart Home Assistant

Home Assistant will update all REST Sensors on startup. It can happen that it tries to read the points before having received a valid token. The sensors will show as unavailable, but after the set interval (5 minutes default value) it will read those sensors again.

## TODO list

Right now it works well enoough for me, and I want to test it before adding additional stuff:

- SECURITY!!! first with RSA encription and then through OAuth2.0
- Adding more sensors from other devices (inverter, meter...)
- What happens if the token is lost? It would just wait more than two days before updating it. The state of the token must be supervised.
