// Section 3 fixture: the Objective-C side of the feature matrix rows that
// Apple's frameworks can't exercise without hardware, permissions or UI.
// Compiled with ARC.
#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>

// F2.1: a struct the user defines, with mixed field types.
typedef struct { int a; float b; char c; } S3Pair;
// F2.2: a union, and a struct with bit fields.
typedef union { int i; float f; } S3Union;
typedef struct { unsigned int a : 3; unsigned int b : 5; unsigned int c : 8; } S3Bits;
// F2.3: a struct holding a fixed-size array.
typedef struct { int v[4]; } S3Quad;

@interface S3Info : NSObject
+ (NSString *)localeCountryCodeKey;
+ (double)foundationVersionNumber;
+ (NSString *)stringFromArrayClass;
@end

@implementation S3Info
+ (NSString *)localeCountryCodeKey { return NSLocaleCountryCode; }
+ (double)foundationVersionNumber { return NSFoundationVersionNumber; }
+ (NSString *)stringFromArrayClass { return NSStringFromClass([NSArray class]); }
@end

@interface S3Types : NSObject
- (S3Pair)echoPair:(S3Pair)value;
- (double)sumRect:(const CGRect *)rect;
- (void)fillRect:(CGRect *)rect;
- (int)unionInt:(S3Union)value;
- (S3Union)makeUnion:(int)value;
- (int)bitsSum:(S3Bits)value;
- (S3Bits)makeBits;
- (int)sumFour:(int[4])values;
- (int)sum:(const int *)values count:(NSUInteger)count;
- (void)fillSquares:(int *)out count:(NSUInteger)count;
- (S3Quad)echoQuad:(S3Quad)value;
- (BOOL)divide:(NSInteger)a by:(NSInteger)b quotient:(NSInteger *)quotient;
- (id)failWithError:(NSError **)error;
- (CGColorRef)makeColor;
- (double)alphaOf:(CGColorRef)color;
- (NSUInteger)countOf:(NSArray *)array;
- (id)valueIn:(NSDictionary *)dict forKey:(NSString *)key;
- (NSArray *)strings;
- (NSArray *)booleans;
- (NSDictionary *)mapping;
@end

@implementation S3Types
- (S3Pair)echoPair:(S3Pair)value { return value; }
- (double)sumRect:(const CGRect *)r { return r->origin.x + r->origin.y + r->size.width + r->size.height; }
- (void)fillRect:(CGRect *)r { *r = CGRectMake(1, 2, 3, 4); }
- (int)unionInt:(S3Union)value { return value.i; }
- (S3Union)makeUnion:(int)value { S3Union u; u.i = value; return u; }
- (int)bitsSum:(S3Bits)v { return (int)(v.a + v.b + v.c); }
- (S3Bits)makeBits { S3Bits b = {5, 17, 200}; return b; }
- (int)sumFour:(int[4])values { return values[0] + values[1] + values[2] + values[3]; }
- (int)sum:(const int *)values count:(NSUInteger)count {
    int total = 0;
    for (NSUInteger i = 0; i < count; i++) total += values[i];
    return total;
}
- (void)fillSquares:(int *)out count:(NSUInteger)count {
    for (NSUInteger i = 0; i < count; i++) out[i] = (int)(i * i);
}
- (S3Quad)echoQuad:(S3Quad)value { return value; }
- (BOOL)divide:(NSInteger)a by:(NSInteger)b quotient:(NSInteger *)q {
    if (b == 0) return NO;
    if (q) *q = a / b;
    return YES;
}
- (id)failWithError:(NSError **)error {
    if (error) *error = [NSError errorWithDomain:@"S3" code:42 userInfo:nil];
    return nil;
}
- (CGColorRef)makeColor { return (CGColorRef)CFAutorelease(CGColorCreateSRGB(0.1, 0.2, 0.3, 0.5)); }
- (double)alphaOf:(CGColorRef)color { return CGColorGetAlpha(color); }
- (NSUInteger)countOf:(NSArray *)array { return [array isKindOfClass:[NSArray class]] ? array.count : NSNotFound; }
- (id)valueIn:(NSDictionary *)dict forKey:(NSString *)key {
    return [dict isKindOfClass:[NSDictionary class]] ? dict[key] : nil;
}
- (NSArray *)strings { return @[@"a", @"b", @"c"]; }
- (NSArray *)booleans { return @[@YES, @NO, @1]; }
- (NSDictionary *)mapping { return @{@"one": @1, @"two": @2}; }
@end

// F3.1, F3.3: Objective-C calling methods that Python defines.
@interface NSObject (S3Python)
- (NSInteger)s3Value;
+ (NSInteger)s3ClassValue;
@end

@interface S3Caller : NSObject
+ (NSInteger)callInstance:(id)object;
+ (NSInteger)callClass:(Class)cls;
+ (NSString *)format:(NSDateFormatter *)formatter;
+ (id)valueOf:(id)object forKey:(NSString *)key;
@end

@implementation S3Caller
+ (NSInteger)callInstance:(id)object { return [object s3Value]; }
+ (NSInteger)callClass:(Class)cls { return [cls s3ClassValue]; }
+ (NSString *)format:(NSDateFormatter *)formatter {
    return [formatter stringFromDate:[NSDate dateWithTimeIntervalSince1970:0]];
}
+ (id)valueOf:(id)object forKey:(NSString *)key { return [object valueForKey:key]; }
@end

// F3.5, F3.7, F4.2: a protocol declared only by this app, never by Apple.
@protocol S3AppProtocol <NSObject>
@optional
- (NSInteger)appValue:(NSInteger)value;
- (int)appUnion:(S3Union)value;
- (int)appArray:(const int *)values count:(NSUInteger)count;
- (BOOL)appShouldContinue:(NSInteger)count;
- (id)appLabel:(NSInteger)count;
- (void)appDecide:(void (^)(BOOL decision))decision;
@end

@interface S3AppCaller : NSObject
+ (Protocol *)protocol;
+ (NSInteger)value:(id<S3AppProtocol>)d of:(NSInteger)v;
+ (int)unionOf:(id<S3AppProtocol>)d value:(int)v;
+ (int)arraySumOf:(id<S3AppProtocol>)d;
+ (BOOL)shouldContinue:(id<S3AppProtocol>)d count:(NSInteger)c;
+ (id)labelOf:(id<S3AppProtocol>)d count:(NSInteger)c;
+ (NSInteger)decisionOf:(id<S3AppProtocol>)d;
@end

@implementation S3AppCaller
+ (Protocol *)protocol { return @protocol(S3AppProtocol); }
+ (NSInteger)value:(id<S3AppProtocol>)d of:(NSInteger)v { return [d appValue:v]; }
+ (int)unionOf:(id<S3AppProtocol>)d value:(int)v { S3Union u; u.i = v; return [d appUnion:u]; }
+ (int)arraySumOf:(id<S3AppProtocol>)d { int v[3] = {2, 3, 4}; return [d appArray:v count:3]; }
+ (BOOL)shouldContinue:(id<S3AppProtocol>)d count:(NSInteger)c { return [d appShouldContinue:c]; }
+ (id)labelOf:(id<S3AppProtocol>)d count:(NSInteger)c { return [d appLabel:c]; }
// Returns 1 for YES, 0 for NO and -1 if the delegate never called the block.
+ (NSInteger)decisionOf:(id<S3AppProtocol>)d {
    __block NSInteger result = -1;
    [d appDecide:^(BOOL decision) { result = decision ? 1 : 0; }];
    return result;
}
@end

// F4.1: a completion handler called later, on another thread.
@interface S3Async : NSObject
- (void)square:(NSInteger)value completion:(void (^)(NSInteger result, NSError *error))completion;
@end

@implementation S3Async
- (void)square:(NSInteger)value completion:(void (^)(NSInteger, NSError *))completion {
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 50 * NSEC_PER_MSEC),
                   dispatch_get_global_queue(QOS_CLASS_DEFAULT, 0), ^{
        completion(value * value, nil);
    });
}
@end

// The Objective-C helper workaround for F4.1: it passes the block itself and
// reports the result to a delegate, which a library without blocks can write.
@protocol S3AsyncHelperDelegate <NSObject>
- (void)helperFinished:(NSInteger)result;
@end

@interface S3AsyncHelper : NSObject
+ (Protocol *)protocol;
+ (void)square:(NSInteger)value delegate:(id<S3AsyncHelperDelegate>)delegate;
@end

@implementation S3AsyncHelper
+ (Protocol *)protocol { return @protocol(S3AsyncHelperDelegate); }
+ (void)square:(NSInteger)value delegate:(id<S3AsyncHelperDelegate>)delegate {
    [[S3Async new] square:value completion:^(NSInteger result, NSError *error) {
        [delegate helperFinished:result];
    }];
}
@end
