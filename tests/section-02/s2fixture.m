// Shared fixture for the Section 2 tests. Compiled without ARC so that
// ownership is explicit. The same code is used for every library.
#import <Foundation/Foundation.h>
#import <CoreGraphics/CoreGraphics.h>
#import <TargetConditionals.h>
#import <objc/runtime.h>
#include <dispatch/dispatch.h>
#include <pthread.h>
#include <unistd.h>

#if TARGET_OS_IPHONE
#import <UIKit/UIGeometry.h>
typedef UIEdgeInsets S2Insets;
#else
typedef NSEdgeInsets S2Insets;
#endif

typedef struct { int a; double b; } S2Inner;
typedef struct { CGPoint origin; NSRange range; S2Inner inner; } S2Nested;

static NSInteger gCreated = 0, gDeallocated = 0;
static char kTrackerKey;

@interface S2Tracked : NSObject <NSCopying>
@property (nonatomic, retain) id strongRef;
+ (void)resetCounts;
+ (NSInteger)createdCount;
+ (NSInteger)deallocCount;
+ (instancetype)newTracked;
+ (instancetype)tracked;
- (NSInteger)value;
@end

@implementation S2Tracked
+ (void)resetCounts { @synchronized (self) { gCreated = 0; gDeallocated = 0; } }
+ (NSInteger)createdCount { @synchronized (self) { return gCreated; } }
+ (NSInteger)deallocCount { @synchronized (self) { return gDeallocated; } }
+ (instancetype)allocWithZone:(NSZone *)zone {
    @synchronized (self) { gCreated++; }
    return [super allocWithZone:zone];
}
+ (instancetype)newTracked { return [[self alloc] init]; }
+ (instancetype)tracked { return [[[self alloc] init] autorelease]; }
- (id)copyWithZone:(NSZone *)zone { return [[S2Tracked alloc] init]; }
- (NSInteger)value { return 42; }
- (void)dealloc {
    [_strongRef release];
    @synchronized ([S2Tracked class]) { gDeallocated++; }
    [super dealloc];
}
@end

@interface S2Holder : NSObject
@property (nonatomic, weak) id weakRef;
- (void)hold:(id)object;
- (id)held;
- (void)releaseHeld;
- (void)attachTrackerTo:(id)object;
- (void)storeWeak:(id)object;
- (id)loadWeak;
@end

@implementation S2Holder {
    id _held;
}
- (void)hold:(id)object { [object retain]; [_held release]; _held = object; }
- (id)held { return _held; }
- (void)releaseHeld { [_held release]; _held = nil; }
- (void)storeWeak:(id)object { self.weakRef = object; }
- (id)loadWeak { return self.weakRef; }
- (void)attachTrackerTo:(id)object {
    S2Tracked *tracker = [[S2Tracked alloc] init];
    objc_setAssociatedObject(object, &kTrackerKey, tracker, OBJC_ASSOCIATION_RETAIN);
    [tracker release];
}
- (void)dealloc { [_held release]; [super dealloc]; }
@end

@interface S2Types : NSObject
- (NSInteger)echoInt:(NSInteger)value;
- (double)echoDouble:(double)value;
- (BOOL)echoBool:(BOOL)value;
- (id)echoObject:(id)value;
- (const char *)echoCString:(const char *)value;
- (Class)echoClass:(Class)value;
- (SEL)echoSelector:(SEL)value;
- (void *)echoPointer:(void *)value;
- (CGRect)echoRect:(CGRect)value;
- (NSRange)echoRange:(NSRange)value;
- (S2Insets)echoInsets:(S2Insets)value;
- (S2Nested)echoNested:(S2Nested)value;
- (void)raiseException;
- (NSInteger)writeOut:(NSInteger *)out;
- (void)sleepFor:(double)seconds;
@end

@implementation S2Types
- (NSInteger)echoInt:(NSInteger)value { return value; }
- (double)echoDouble:(double)value { return value; }
- (BOOL)echoBool:(BOOL)value { return value; }
- (id)echoObject:(id)value { return value; }
- (const char *)echoCString:(const char *)value { return value; }
- (Class)echoClass:(Class)value { return value; }
- (SEL)echoSelector:(SEL)value { return value; }
- (void *)echoPointer:(void *)value { return value; }
- (CGRect)echoRect:(CGRect)value { return value; }
- (NSRange)echoRange:(NSRange)value { return value; }
- (S2Insets)echoInsets:(S2Insets)value { return value; }
- (S2Nested)echoNested:(S2Nested)value { return value; }
- (void)raiseException { [NSException raise:@"S2Exception" format:@"raised by fixture"]; }
- (NSInteger)writeOut:(NSInteger *)out { if (out) *out = 7; return 1; }
- (void)sleepFor:(double)seconds { usleep((useconds_t)(seconds * 1000000)); }
@end

@protocol S2Delegate <NSObject>
@optional
- (NSInteger)delegateInt:(NSInteger)value;
- (double)delegateDouble:(double)value;
- (id)delegateObject:(id)value;
- (CGRect)delegateRect:(CGRect)value;
- (void)delegateFired;
- (void)delegateTakeBlock:(NSInteger (^)(NSInteger))block;
@end

// Base class for Python subclasses. Every method returns a marker value, so
// that a result from Python can be told apart from the base implementation.
@interface S2Overridable : NSObject <S2Delegate>
@end

@implementation S2Overridable
- (NSInteger)delegateInt:(NSInteger)value { return -1; }
- (double)delegateDouble:(double)value { return -1.0; }
- (id)delegateObject:(id)value { return nil; }
- (CGRect)delegateRect:(CGRect)value { return CGRectZero; }
- (void)delegateFired {}
- (void)delegateTakeBlock:(NSInteger (^)(NSInteger))block {}
@end

static void *fireOnThread(void *arg) {
    id<S2Delegate> delegate = arg;
    @autoreleasepool { [delegate delegateFired]; }
    [delegate release];
    return NULL;
}

static void *fireAndSignal(void *arg) {
    NSArray *pair = arg;
    id<S2Delegate> delegate = pair[0];
    dispatch_semaphore_t done = pair[1];
    @autoreleasepool { [delegate delegateFired]; }
    dispatch_semaphore_signal(done);
    [pair release];
    return NULL;
}

@interface S2Caller : NSObject
+ (Protocol *)delegateProtocol;
- (NSInteger)callInt:(id<S2Delegate>)delegate value:(NSInteger)value;
- (double)callDouble:(id<S2Delegate>)delegate value:(double)value;
- (id)callObject:(id<S2Delegate>)delegate value:(id)value;
- (CGRect)callRect:(id<S2Delegate>)delegate value:(CGRect)value;
- (void)fireOnGCD:(id<S2Delegate>)delegate;
- (void)fireOnPthread:(id<S2Delegate>)delegate;
- (void)fireOnPthreadAndWait:(id<S2Delegate>)delegate;
- (void)retainDelegate:(id<S2Delegate>)delegate;
- (NSInteger)callRetainedInt:(NSInteger)value;
- (void)dropDelegate;
- (void)offerBlockTo:(id<S2Delegate>)delegate;
- (void)offerStackBlockTo:(id<S2Delegate>)delegate;
@end

@implementation S2Caller {
    id<S2Delegate> _retained;
}
+ (Protocol *)delegateProtocol { return @protocol(S2Delegate); }
- (NSInteger)callInt:(id<S2Delegate>)d value:(NSInteger)v { return [d delegateInt:v]; }
- (double)callDouble:(id<S2Delegate>)d value:(double)v { return [d delegateDouble:v]; }
- (id)callObject:(id<S2Delegate>)d value:(id)v { return [d delegateObject:v]; }
- (CGRect)callRect:(id<S2Delegate>)d value:(CGRect)v { return [d delegateRect:v]; }
- (void)fireOnGCD:(id<S2Delegate>)d {
    [d retain];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_DEFAULT, 0), ^{
        [d delegateFired];
        [d release];
    });
}
- (void)fireOnPthread:(id<S2Delegate>)d {
    pthread_t thread;
    [d retain];
    pthread_create(&thread, NULL, fireOnThread, d);
    pthread_detach(thread);
}
- (void)fireOnPthreadAndWait:(id<S2Delegate>)d {
    pthread_t thread;
    dispatch_semaphore_t done = dispatch_semaphore_create(0);
    NSArray *pair = [[NSArray alloc] initWithObjects:d, done, nil];
    pthread_create(&thread, NULL, fireAndSignal, pair);
    pthread_detach(thread);
    dispatch_semaphore_wait(done, DISPATCH_TIME_FOREVER);
    dispatch_release(done);
}
- (void)retainDelegate:(id<S2Delegate>)d { [d retain]; [_retained release]; _retained = d; }
- (NSInteger)callRetainedInt:(NSInteger)v { return [_retained delegateInt:v]; }
- (void)dropDelegate { [_retained release]; _retained = nil; }
- (void)offerBlockTo:(id<S2Delegate>)d {
    NSInteger captured = 100;
    NSInteger (^block)(NSInteger) = ^NSInteger(NSInteger x) { return x + captured; };
    NSInteger (^heap)(NSInteger) = [block copy];
    [d delegateTakeBlock:heap];
    [heap release];
}
- (void)offerStackBlockTo:(id<S2Delegate>)d {
    NSInteger captured = 100;
    [d delegateTakeBlock:^NSInteger(NSInteger x) { return x + captured; }];
}
- (void)dealloc { [_retained release]; [super dealloc]; }
@end

typedef NSInteger (^S2IntBlock)(NSInteger);
typedef double (^S2DoubleBlock)(double);
typedef id (^S2ObjectBlock)(id);
typedef CGRect (^S2RectBlock)(CGRect);
typedef void (^S2VoidBlock)(void);

@interface S2Blocks : NSObject
- (NSInteger)callInt:(S2IntBlock)block value:(NSInteger)value;
- (double)callDouble:(S2DoubleBlock)block value:(double)value;
- (id)callObject:(S2ObjectBlock)block value:(id)value;
- (CGRect)callRect:(S2RectBlock)block value:(CGRect)value;
- (double)callRectArg:(double (^)(CGRect))block value:(CGRect)value;
- (void)storeInt:(S2IntBlock)block;
- (NSInteger)callStoredInt:(NSInteger)value;
- (void)dropStored;
- (void)callOnPthreadAndWait:(S2VoidBlock)block;
- (S2IntBlock)makeIntBlock;
- (S2DoubleBlock)makeDoubleBlock;
- (S2ObjectBlock)makeObjectBlock;
- (S2RectBlock)makeRectBlock;
- (S2VoidBlock)makeThrowingBlock;
@end

static void *callBlockAndSignal(void *arg) {
    NSArray *pair = arg;
    S2VoidBlock block = pair[0];
    dispatch_semaphore_t done = pair[1];
    @autoreleasepool { block(); }
    dispatch_semaphore_signal(done);
    [pair release];
    return NULL;
}

@implementation S2Blocks {
    S2IntBlock _stored;
}
- (NSInteger)callInt:(S2IntBlock)block value:(NSInteger)v { return block(v); }
- (double)callDouble:(S2DoubleBlock)block value:(double)v { return block(v); }
- (id)callObject:(S2ObjectBlock)block value:(id)v { return block(v); }
- (CGRect)callRect:(S2RectBlock)block value:(CGRect)v { return block(v); }
- (double)callRectArg:(double (^)(CGRect))block value:(CGRect)v { return block(v); }
- (void)storeInt:(S2IntBlock)block { [_stored release]; _stored = [block copy]; }
- (NSInteger)callStoredInt:(NSInteger)v { return _stored(v); }
- (void)dropStored { [_stored release]; _stored = nil; }
- (void)callOnPthreadAndWait:(S2VoidBlock)block {
    pthread_t thread;
    dispatch_semaphore_t done = dispatch_semaphore_create(0);
    NSArray *pair = [[NSArray alloc] initWithObjects:[[block copy] autorelease], done, nil];
    pthread_create(&thread, NULL, callBlockAndSignal, pair);
    pthread_detach(thread);
    dispatch_semaphore_wait(done, DISPATCH_TIME_FOREVER);
    dispatch_release(done);
}
- (S2IntBlock)makeIntBlock {
    NSInteger captured = 1;
    return [[^NSInteger(NSInteger x) { return x + captured; } copy] autorelease];
}
- (S2DoubleBlock)makeDoubleBlock {
    return [[^double(double x) { return x * 2; } copy] autorelease];
}
- (S2ObjectBlock)makeObjectBlock {
    return [[^id(id x) { return x; } copy] autorelease];
}
- (S2RectBlock)makeRectBlock {
    return [[^CGRect(CGRect r) { return r; } copy] autorelease];
}
- (S2VoidBlock)makeThrowingBlock {
    return [[^{ [NSException raise:@"S2Exception" format:@"raised by block"]; } copy] autorelease];
}
- (void)dealloc { [_stored release]; [super dealloc]; }
@end

typedef NSInteger (*S2IntFunction)(NSInteger);
typedef double (*S2DoubleFunction)(double);
typedef id (*S2ObjectFunction)(id);
typedef CGRect (*S2RectFunction)(CGRect);

@interface S2Functions : NSObject
- (NSInteger)callInt:(S2IntFunction)function value:(NSInteger)value;
- (double)callDouble:(S2DoubleFunction)function value:(double)value;
- (id)callObject:(S2ObjectFunction)function value:(id)value;
- (CGRect)callRect:(S2RectFunction)function value:(CGRect)value;
- (double)callRectArg:(double (*)(CGRect))function value:(CGRect)value;
- (void)storeInt:(S2IntFunction)function;
- (NSInteger)callStoredInt:(NSInteger)value;
@end

@implementation S2Functions {
    S2IntFunction _stored;
}
- (NSInteger)callInt:(S2IntFunction)f value:(NSInteger)v { return f(v); }
- (double)callDouble:(S2DoubleFunction)f value:(double)v { return f(v); }
- (id)callObject:(S2ObjectFunction)f value:(id)v { return f(v); }
- (CGRect)callRect:(S2RectFunction)f value:(CGRect)v { return f(v); }
- (double)callRectArg:(double (*)(CGRect))f value:(CGRect)v { return f(v); }
- (void)storeInt:(S2IntFunction)f { _stored = f; }
- (NSInteger)callStoredInt:(NSInteger)v { return _stored(v); }
@end
