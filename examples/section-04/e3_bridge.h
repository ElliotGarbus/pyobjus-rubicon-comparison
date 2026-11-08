// E3's helper for pyobjus: kivy-ios's project template bridge.h, trimmed to
// the altimeter.
#import <Foundation/Foundation.h>
#import <CoreMotion/CoreMotion.h>

@interface bridge : NSObject {
    NSOperationQueue *queue;
}

@property (nonatomic) double relative_altitude;
@property (nonatomic) double pressure;

@end
