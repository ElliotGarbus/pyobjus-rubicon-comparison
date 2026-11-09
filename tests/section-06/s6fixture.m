// Shared fixture for the Section 6 benchmarks. Compiled without ARC, as
// Section 2's fixture is. Every library calls the same methods.
#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>
#import <objc/runtime.h>

static NSInteger gItemsCreated = 0, gItemsDeallocated = 0;

// Objects created and dropped for the memory measurements (M2 to M4).
@interface S6Item : NSObject <NSCopying>
+ (void)resetCounts;
+ (NSInteger)createdCount;
+ (NSInteger)deallocCount;
+ (instancetype)item;
@end

@implementation S6Item
+ (void)resetCounts { gItemsCreated = 0; gItemsDeallocated = 0; }
+ (NSInteger)createdCount { return gItemsCreated; }
+ (NSInteger)deallocCount { return gItemsDeallocated; }
+ (instancetype)allocWithZone:(NSZone *)zone {
    gItemsCreated++;
    return [super allocWithZone:zone];
}
+ (instancetype)item { return [[[self alloc] init] autorelease]; }
- (id)copyWithZone:(NSZone *)zone { return [[S6Item alloc] init]; }
- (void)dealloc {
    gItemsDeallocated++;
    [super dealloc];
}
@end

// Calls from Python (C1 to C4, M4).
@interface S6Target : NSObject
@property (nonatomic) NSInteger value;
+ (void)classNoop;
- (void)noop;
- (NSInteger)echoInt:(NSInteger)v;
- (double)echoDouble:(double)v;
- (BOOL)echoBool:(BOOL)v;
- (id)echoObject:(id)v;
- (CGRect)echoRect:(CGRect)v;
- (NSString *)echoString:(NSString *)v;
- (S6Item *)makeItem;
@end

@implementation S6Target
+ (void)classNoop {}
- (void)noop {}
- (NSInteger)echoInt:(NSInteger)v { return v; }
- (double)echoDouble:(double)v { return v; }
- (BOOL)echoBool:(BOOL)v { return v; }
- (id)echoObject:(id)v { return v; }
- (CGRect)echoRect:(CGRect)v { return v; }
- (NSString *)echoString:(NSString *)v { return v; }
- (S6Item *)makeItem { return [S6Item item]; }
@end

// Calls from Objective-C to Python (CB1, M3 delegates).
@protocol S6Delegate <NSObject>
@optional
- (void)delegateNoop;
- (NSInteger)delegateInt:(NSInteger)v;
- (void)delegateObject:(id)v;
@end

@interface S6Caller : NSObject
+ (Protocol *)delegateProtocol;
- (void)callNoop:(id<S6Delegate>)d times:(NSInteger)n;
- (NSInteger)callInt:(id<S6Delegate>)d times:(NSInteger)n;
- (void)callObject:(id<S6Delegate>)d argument:(id)object times:(NSInteger)n;
- (void)useDelegate:(id<S6Delegate>)d;
@end

@implementation S6Caller
+ (Protocol *)delegateProtocol { return @protocol(S6Delegate); }
- (void)callNoop:(id<S6Delegate>)d times:(NSInteger)n {
    @autoreleasepool { for (NSInteger i = 0; i < n; i++) [d delegateNoop]; }
}
- (NSInteger)callInt:(id<S6Delegate>)d times:(NSInteger)n {
    NSInteger total = 0;
    @autoreleasepool { for (NSInteger i = 0; i < n; i++) total += [d delegateInt:i]; }
    return total;
}
- (void)callObject:(id<S6Delegate>)d argument:(id)object times:(NSInteger)n {
    @autoreleasepool { for (NSInteger i = 0; i < n; i++) [d delegateObject:object]; }
}
- (void)useDelegate:(id<S6Delegate>)d { [d delegateNoop]; }
@end

// First use (C5): classes no other measurement touches, one with 5 instance
// methods and one with 100, each with a class method to call first.
#define S6M(n) - (NSInteger)method##n { return n; }
#define S6M5 S6M(1) S6M(2) S6M(3) S6M(4) S6M(5)
#define S6M10(a) S6M(a##0) S6M(a##1) S6M(a##2) S6M(a##3) S6M(a##4) S6M(a##5) S6M(a##6) S6M(a##7) \
    S6M(a##8) S6M(a##9)

@interface S6Fresh5 : NSObject
+ (NSInteger)fresh;
@end
@implementation S6Fresh5
+ (NSInteger)fresh { return 5; }
S6M5
@end

@interface S6Fresh100 : NSObject
+ (NSInteger)fresh;
@end
@implementation S6Fresh100
+ (NSInteger)fresh { return 100; }
S6M10(1) S6M10(2) S6M10(3) S6M10(4) S6M10(5) S6M10(6) S6M10(7) S6M10(8) S6M10(9) S6M10(10)
@end
