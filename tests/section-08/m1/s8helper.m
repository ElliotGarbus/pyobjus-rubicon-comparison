// A class an app supplies itself, like Plyer's bridge or Ren'Py's IAPHelper.
// Build: xcrun --sdk macosx clang -dynamiclib -arch arm64 -fobjc-arc
//        -framework Foundation s8helper.m -o libs8helper.dylib
#import <Foundation/Foundation.h>

@interface S8Helper : NSObject
@property (nonatomic) double level;
+ (NSString *)greet:(NSString *)name;
- (void)bump;
@end

@implementation S8Helper
+ (NSString *)greet:(NSString *)name {
    return [@"hello, " stringByAppendingString:name];
}
- (void)bump {
    self.level += 0.5;
}
@end
