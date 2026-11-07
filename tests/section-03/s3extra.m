// F1.6: a dylib the app builds and loads at runtime. The runner doesn't load
// it, so a class here is found only if the library loads the file.
#import <Foundation/Foundation.h>

@interface S3Extra : NSObject
+ (NSInteger)answer;
@end

@implementation S3Extra
+ (NSInteger)answer { return 42; }
@end
