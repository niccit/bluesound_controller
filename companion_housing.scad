// SPDX-License-Identifier: MIT
$fa = 1;
$fs = 0.4;

include <YAPP_Box/YAPPgenerator_v3.scad>

// Housing for Bluesound controller
// Components:
//   LiPoly Battery - 34mm x 62mm - determines the length of the project
//   4 Key NeoPixel Keyboard  - 76.5mm x 21mm - determines the width of the project
//   Rotary encoder board  - 25.6mm x 25.3mm x 4.6mm - Encoder dimensions 14.38mm x 12.72 _stepper_motor_mount
//      Knob diameter 6.93mm
//   Feather ESP32-S3 - 52.3mm x 22.7mm x 2.1mm

printBaseShell = true;
printLidShell  = true;
showPCB = true;

pcbLength = 52.3; // Front to back
pcbWidth = 22.7; // Side to side
pcbThickness = 2.1;

//-- padding between pcb and inside wall
paddingFront = 5;
paddingBack = 5;
paddingRight = 10;
paddingLeft = 5;

wallThickness = 2.4;
basePlaneThickness = 4.0;
lidPlaneThickness = 2;

baseWallHeight = 15;
lidWallHeight = 20;

ridgeHeight = 5;
ridgeSlack = 0.2;
roundRadius = 0.1;

standoffHeight = 5;  //-- used for PCB Supports, Push Button and showPCB
standoffDiameter= 5;
standoffPinDiameter = 2.5;
standoffHoleSlack = 0.4;

pcb = [
   ["Main", pcbWidth, pcbLength, 0, 0, pcbThickness, standoffHeight, standoffDiameter, standoffPinDiameter, standoffHoleSlack]
   ,["Battery", 34, 62, pcbWidth + 2, 8, 5, 0, 0, 0, 0, 0]
];

pcbStands = [
   [2, 3.25, standoffHeight, default, standoffDiameter, 2, yappAllCorners, yappBaseOnly, yappHole, yappSelfThreading]
   ,[39.25, 18.5, 29, 3, yappLidOnly, yappHole, yappSelfThreading, yappNoFillet]   // Left back keyboard
   ,[55.75, 18.5, 29, 3, yappLidOnly, yappHole, yappSelfThreading, yappNoFillet]   // Left front keyboard
   ,[39.25, 56.5, 29, 3, yappLidOnly, yappHole, yappSelfThreading, yappNoFillet]   // Right back keyboard
   ,[55.75, 56.5, 29, 3, yappLidOnly, yappHole, yappSelfThreading, yappNoFillet]   // Right front keyboard
   ,[7, 17, 25, yappLidOnly, yappHole, yappSelfThreading]    // Left back rotary
   ,[7, 37.5, 25, yappLidOnly, yappHole, yappSelfThreading]    // Right back rotary
   ,[27.25, 17, 25, yappLidOnly, yappHole, yappSelfThreading]    // Left front rotary
   ,[27.25, 37.5, 25, yappLidOnly, yappHole, yappSelfThreading]    // Right front rotary
   ];

cutoutsBase = [
   [ 55 / 2 + 15, 76.5 / 2, 30, 35, 0, yappRectangle, maskHoneycomb, yappCenter]   // venting
   ];

cutoutsLeft = [
   [11, 2, 12, 8, 0, yappRectangle, yappCenter, yappCoordPCB]  // USB power
   ];

cutoutsRight = [
   [11, 13, 10, 10, 3.9, yappCircle, yappCenter, yappLidOnly]  // wake from sleep alarm
];

cutoutsLid = [
   [40, 1, 15, 73 , 0, yappRectangle]    // Keyboard
   ,[11, 21, 0, 0, 6, yappCircle]         // Rotary Encoder
   ];

snapJoins = [
   [shellLength / 2, 5, yappLeft, yappRight, yappSymmetric, yappRectangle]
   ,[shellWidth / 2, 5, yappFront, yappBack, yappSymmetric, yappRectangle]
   ];

// labelsPlane = [
//    [38, 21, 90, 1, yappLid, "Liberation Mono:style=bold", 4, "VOL/MUTE"]
//    ,[67, 6, 90, 1, yappLid, "liberation Mono:style=bold", 3, "OPTICAL"]
//    ,[67, 28, 90, 1, yappLid, "liberation Mono:style=bold", 3, "HDMI"]
//    ,[67, 66, 90, 1, yappLid, "liberation Mono:style=bold", 3, "ALOHA"]
//    ,[71, 68, 90, 1, yappLid, "liberation Mono:style=bold", 3, "JOE"]
//    ];

module key_plate() {
    cube([73, 10, 2], center=true);
    translate([-35.5, -1.5, 1 - 0.01])
    linear_extrude(1)
        color("blue")text("OPT", font = "Liberation Sans", size = 4.5);
    translate([-17, -1.5, 1 - 0.01])
    linear_extrude(1)
        color("blue")text("HDMI", font = "Liberation Sans", size = 4.5);
    translate([5, -1.5, 1 - 0.01])
    linear_extrude(1)
        color("blue")text("PRNL", font = "Liberation Sans", size = 4);
    translate([25, -1.25, 1 - 0.01])
    linear_extrude(1)
        color("blue")text("AJ", font = "Liberation Sans", size = 4);
}

module volume_plate() {
    cube([20, 14, 2], center=true);
    translate([-7, 1.5, 1 - 0.01])
    linear_extrude(1)
        color("red")text("VOL /", font = "Liberation Sans", size = 4.5);
    translate([-8.5, -5, 1 - 0.01])
    linear_extrude(1)
        color("red")text("MUTE", font = "Liberation Sans", size = 4.5);
}

// Set to true if you want to create separate lable plates for the project
show_all = true;
show_labels = false;
show_case = false;

if (show_all == true) {
    YAPPgenerate();
    translate([40, -15, 0])
        key_plate();
    translate([40, -30, 0])
        volume_plate();
}

if (show_case == true) {
    YAPPgenerate();
}

if (show_labels == true) {
    key_plate();
    translate([0, -20, 0])
        volume_plate();
}
