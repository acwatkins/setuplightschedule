#!/usr/bin/env ruby

require 'rubygems'
require 'huey'
require_relative 'hueLevels.rb'
require_relative 'Home.rb'

home = new Home

# 5:45
puts "Turning lights orange red"
home.masterBedroomHers.update(on: true, rgb: RGB_ORANGE_RED, bri: 0)
sleep(10)

# 5:45 - 6:20
sleep(35 * 60)
home.masterBedroomHers.update(on: false)

# 6:45 - 7:10
puts "Beginning 25 min transition to yellow sun"
home.masterBedroom.update(rgb: RGB_YELLOW_SUN, bri: BRI_RELAX, transitiontime: 24 * 60 * 10)
sleep(25 * 60)

# 7:10 - 7:11
puts "Beginning 1 min transition to Relax"
home.masterBedroom.update(ct: CT_RELAX, bri: BRI_RELAX, transitiontime: 50 * 10)
sleep(60)

# 7:11 - 7:13
puts "Beginning 2 min transition to Reading"
home.masterBedroom.update(ct: CT_READING, bri: BRI_READING, transitiontime: 110 * 10)
sleep(2 * 60)

# 7:13 - 7:14
puts "Beginning 1 minute transition to white light"
home.masterBedroom.update(rgb: '#FFFFFF', bri: BRI_CONCENTRATE, transitiontime: 50 * 10)
sleep(60)

# 7:14 - 7:15
puts "Beginning 1 minute transition to Energize"
home.masterBedroom.update(ct: CT_ENERGIZE, bri: BRI_ENERGIZE, transitiontime: 50 * 10)
sleep(60)