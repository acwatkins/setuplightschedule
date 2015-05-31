#!/usr/bin/env python3

import datetime
import huelevels
import hues
import logging
import pytz
import time
from astral import Astral
from phue import Bridge

logging.basicConfig(level=logging.INFO)

hues.setTimezone(pytz.timezone("America/New_York"))
schedule = hues.Schedule('huebridge', 'newdeveloper')
astral = Astral()
astral.solar_depression = 'civil'
city = astral["Orlando"]
sunToday = city.sun(date = datetime.date.today(), local = True)
sunTomorrow = city.sun(date = datetime.date.today() + datetime.timedelta(days = 1), local = True)
sunsetTime = sunToday["sunset"]
sunriseTime = sunTomorrow["sunrise"]
sunriseLightsTransitionTime = sunriseTime + datetime.timedelta(minutes = 30)
sunriseLightsOffTime = sunriseTime + datetime.timedelta(minutes = 60)
sunsetLightsOnTime = sunsetTime - datetime.timedelta(minutes = 60)

allLights = ["MasterBedroomHers", "FamilyRoomLeft", "FamilyRoomRight", "MasterBedroomHis", "FamilyRoomTorch"]
familyRoom = ["FamilyRoomLeft", "FamilyRoomRight", "FamilyRoomTorch"]
masterBedroom = ["MasterBedroomHers", "MasterBedroomHis"]

def transitionRelaxToEnergize(beginDateTime, endDateTime, lightNames):
	logging.info("Transitioning from Relax to Energize")
	logging.info("beginDateTime: " + str(beginDateTime))
	logging.info("endDateTime: " + str(endDateTime))

	if (endDateTime > sunriseTime):
		logging.info("endDateTime after sunrise, reseting to sunrise")
		endDateTime = sunriseTime

	if (endDateTime < beginDateTime):
		logging.info("transition time negative, setting end time to latest")
		endDateTime = sunriseLightsTransitionTime
		logging.info("beginDateTime: " + str(beginDateTime))
		logging.info("endDateTime: " + str(endDateTime))

	deltaDateTime = endDateTime - beginDateTime
	deltaDateTimeInSeconds = deltaDateTime / datetime.timedelta(seconds = 1)

	secondsPerTransition = int(deltaDateTimeInSeconds / 3)
	durationBetweenEventsInDeciseconds = secondsPerTransition * 10
	transitionTimeInDeciseconds = (secondsPerTransition - 1) * 10
	logging.info("deltaTime: " + str(deltaDateTime))
	logging.info("minutesPerTransition: " + str(secondsPerTransition / 60))

	if (deltaDateTimeInSeconds > 0 and endDateTime <= sunriseLightsTransitionTime):
		schedule.addGroupEvent(beginDateTime, lightNames, 'reading', transitionTimeInDeciseconds)
		schedule.addGroupEventByOffsetToLast(durationBetweenEventsInDeciseconds, lightNames, 'white', transitionTimeInDeciseconds)
		schedule.addGroupEventByOffsetToLast(durationBetweenEventsInDeciseconds, lightNames, 'energize', transitionTimeInDeciseconds)
		schedule.addGroupEvent(sunriseLightsTransitionTime, lightNames, 'energize', 30 * 60 * 10)

def transitionEnergizeToRelax(beginDateTime, endDateTime, lightNames):
	logging.info("Transitioning from Energize to Relax")
	logging.debug("beginDateTime: " + str(beginDateTime))
	logging.debug("endDateTime: " + str(endDateTime))
	deltaDateTime = endDateTime - beginDateTime
	deltaDateTimeInSeconds = deltaDateTime / datetime.timedelta(seconds = 1)

	secondsPerTransition = int(deltaDateTimeInSeconds / 3)
	durationBetweenEventsInDeciseconds = secondsPerTransition * 10
	transitionTimeInDeciseconds = (secondsPerTransition - 1) * 10
	logging.info("deltaTime: " + str(deltaDateTime))
	logging.info("minutesPerTransition: " + str(secondsPerTransition / 60))

	schedule.addGroupEvent(beginDateTime, lightNames, 'white', 30 * 10)
	schedule.addGroupEventByOffsetToLast(durationBetweenEventsInDeciseconds, lightNames, 'reading', transitionTimeInDeciseconds)
	schedule.addGroupEventByOffsetToLast(durationBetweenEventsInDeciseconds, lightNames, 'relax', transitionTimeInDeciseconds)

def morningRoutine(beginDateTime, lightNames):
	currentTime = beginDateTime

	if (currentTime < sunriseLightsOffTime):
		schedule.addGroupEvent(currentTime, lightNames, 'orangeLow', 0, lightOn = True)

	currentTime += datetime.timedelta(minutes = 15)

	if (currentTime < sunriseLightsOffTime):
		schedule.addGroupEvent(currentTime, lightNames, 'yellowSun', 9 * 60 * 10)

	currentTime += datetime.timedelta(minutes = 10)

	if (currentTime < sunriseLightsOffTime):
		schedule.addGroupEvent(currentTime, lightNames, 'relax', 4 * 60 * 10)

	currentTime += datetime.timedelta(minutes = 5)
	endTime = currentTime + datetime.timedelta(minutes = 15)
	transitionRelaxToEnergize(currentTime, endTime, lightNames)

def bedTimeRoutine(beginDateTime, lightNames):
	currentTime = beginDateTime

	schedule.addGroupEvent(currentTime, lightNames, 'yellowSun', 29 * 60 * 10)
	currentTime += datetime.timedelta(minutes = 30)
	schedule.addGroupEvent(currentTime, lightNames, 'orangeLow', 15 * 60 * 10)
	currentTime += datetime.timedelta(minutes = 20)
	for light in lightNames:
		schedule.addEvent(currentTime, light, 'orangeLow', 0, lightOn = False)
		currentTime += datetime.timedelta(minutes = 5)

def setupSchedule(bedTimeHis, bedTimeHers, sleepDurationHis, sleepDurationHers):
	bridge = Bridge('huebridge', 'newdeveloper')
	# bridge.connect()
	#bridge.get_api()

	# lightsByName = bridge.get_light_objects('name')
	# for light in lightsByName:
	# 	print(str(light))

	schedules = bridge.get_schedule()
	logging.info("Removing old schedules")
	for i in schedules:
		bridge.delete_schedule(i)

	logging.info(sunsetLightsOnTime.strftime("%H:%M:%S turn on lights"))
	schedule.addGroupEvent(sunsetLightsOnTime, allLights, 'energize', 30 * 60 * 10, lightOn = True)

	logging.info("sunset is at " + str(sunsetTime))
	transitionEnergizeToRelax(sunsetTime, bedTimeHers - datetime.timedelta(hours = 1), allLights)

	bedTimeStartTimeMasterBedroom = bedTimeHers - datetime.timedelta(minutes = 30)
	bedTimeStartTimeFamilyRoom = bedTimeHis - datetime.timedelta(minutes = 30)
	if (bedTimeHis != bedTimeHers):
		bedTimeRoutine(bedTimeStartTimeMasterBedroom, masterBedroom)
		bedTimeRoutine(bedTimeStartTimeFamilyRoom, familyRoom)

		turnOnMasterBedroomLightTime = bedTimeHis - datetime.timedelta(minutes = 15)
		turnOffMasterBedroomLightTime = bedTimeHis + datetime.timedelta(minutes = 30)
		schedule.addEvent(turnOnMasterBedroomLightTime, 'MasterBedroomHis', 'orangeLow', 0, lightOn = True)
		schedule.addEvent(turnOffMasterBedroomLightTime, 'MasterBedroomHis', 'orangeLow', 0, lightOn = False)
	else:
		bedTimeRoutine(bedTimeStartTimeFamilyRoom, allLights)

	wakeUpTimeHis = bedTimeHis + datetime.timedelta(hours = sleepDurationHis)
	wakeUpTimeHers = bedTimeHers + datetime.timedelta(hours = sleepDurationHers)
	if (wakeUpTimeHis != wakeUpTimeHers):
		lightsOnHers = wakeUpTimeHers - datetime.timedelta(minutes = 15)
		lightsOffHers = wakeUpTimeHers + datetime.timedelta(minutes = 30)
		schedule.addEvent(lightsOnHers, 'MasterBedroomHers', 'orangeLow', 0, lightOn = True)
		schedule.addEvent(lightsOffHers, 'MasterBedroomHers', 'orangeLow', 0, lightOn = False)

		morningRoutine(lightsOnHers, familyRoom)
		lightsOnHis = wakeUpTimeHis - datetime.timedelta(minutes = 15)
		morningRoutine(lightsOnHis, masterBedroom)
	else:
		lightsOnTime = wakeUpTimeHers - datetime.timedelta(minutes = 15)
		morningRoutine(lightsOnTime, allLights)

	logging.info("sunrise is at " + str(sunriseTime))
	logging.info(sunriseLightsOffTime.strftime("%H:%M:%S turn off lights"))
	schedule.addGroupEvent(sunriseLightsOffTime, allLights, 'energize', 0, lightOn = False)


if __name__ == '__main__':
	weekday = datetime.datetime.now().weekday()
	bedTimeHers = hues.LocalDateTime(22, 0, 0)
	bedTimeHis = bedTimeHers
	sleepDurationHis = 8
	sleepDurationHers = 8
	if (weekday == 4 or weekday == 5):
		bedTimeHis = hues.LocalDateTime(23, 0, 0)
	elif (weekday == 0):
		bedTimeHis = hues.LocalDateTime(0, 0, 0, datetime.datetime.today() + datetime.timedelta(days = 1))
		sleepDurationHis = 7

	setupSchedule(bedTimeHis, bedTimeHers, sleepDurationHis, sleepDurationHers)
