// E3's helper for pyobjus: kivy-ios's project template bridge.m, trimmed to
// the altimeter. Compiled with manual reference counting, as the template is.
#import "e3_bridge.h"

@implementation bridge

CMAltimeter *altimeterManager;

- (id) init {
    if(self = [super init]) {
        queue = [[NSOperationQueue alloc] init];
    }
    return self;
}

- (void)startRelativeAltitude {

    if ([CMAltimeter isRelativeAltitudeAvailable]) {
        altimeterManager = [[CMAltimeter alloc] init];
        [altimeterManager startRelativeAltitudeUpdatesToQueue:queue withHandler:^(CMAltitudeData *altitudeData, NSError *error) {
            self.relative_altitude = altitudeData.relativeAltitude.floatValue;
            self.pressure = altitudeData.pressure.floatValue;
        }];
    }
}

- (void) stopRelativeAltitude {
    [altimeterManager stopRelativeAltitudeUpdates];
}

- (void) dealloc {
    [queue release];
    [super dealloc];
}

@end
