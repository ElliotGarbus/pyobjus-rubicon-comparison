// The same T5 calls in Objective-C, for the entries whose right answer isn't obvious.
// t5_calls.py takes its expected values from this output.
// Build: xcrun clang -fobjc-arc -framework AppKit t5_truth.m -o t5_truth
#import <AppKit/AppKit.h>

int main(void) {
    @autoreleasepool {
        NSString *dir = NSTemporaryDirectory();
        NSString *file = [dir stringByAppendingPathComponent:@"s2t5truth.txt"];
        [@"hello" writeToFile:file atomically:NO encoding:NSUTF8StringEncoding error:NULL];
        NSError *err = nil;
        id value = nil;
        NSString *desc = nil;

        NSLinguisticTagger *tagger = [[NSLinguisticTagger alloc] initWithTagSchemes:@[@"TokenType"] options:0];
        tagger.string = @"a b";
        [tagger enumerateTagsInRange:NSMakeRange(0, 3) unit:0 scheme:@"TokenType" options:0
                          usingBlock:^(NSLinguisticTag t, NSRange r, BOOL *s) {
            printf("22 %s %lu %lu\n", t.UTF8String, r.location, r.length);
        }];
        BOOL ok = [[NSPersonNameComponentsFormatter new] getObjectValue:&value forString:@"Ann Lee" errorDescription:&desc];
        printf("30 %d given=%s\n", ok, [value givenName].UTF8String);
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
        desc = nil;
        NSData *plist = [NSPropertyListSerialization dataFromPropertyList:[NSObject new] format:NSPropertyListXMLFormat_v1_0 errorDescription:&desc];
        printf("33 data=%p desc=%s\n", plist, desc.UTF8String);
        NSStringEncoding enc = 0;
        NSString *t = [[NSString alloc] initWithContentsOfFile:file usedEncoding:&enc error:&err];
        printf("37 %s enc=%lu err=%p\n", t.UTF8String, enc, err);
        NSString *partial = @"1"; desc = nil;
        printf("38 %d\n", [[NSNumberFormatter new] isPartialStringValid:@"1" newEditingString:&partial errorDescription:&desc]);
        value = nil; desc = nil;
        printf("40 %d\n", [[NSDateComponentsFormatter new] getObjectValue:&value forString:@"1" errorDescription:&desc]);
        NSInputStream *in = nil; NSOutputStream *out = nil;
        [NSStream getStreamsToHost:[NSHost hostWithName:@"localhost"] port:9 inputStream:&in outputStream:&out];
        printf("44 %d %d\n", in != nil, out != nil);
        NSDictionary *info = nil;
        id script = [[NSAppleScript alloc] initWithContentsOfURL:[NSURL fileURLWithPath:@"/no/such/s2"] error:&info];
        printf("45 %p info=%d\n", script, info != nil);
        NSXMLDocument *doc = [[NSXMLDocument alloc] initWithXMLString:@"<a/>" options:0 error:NULL];
        err = nil;
        id xslt = [doc objectByApplyingXSLTString:@"not xslt" arguments:nil error:&err];
        printf("46 %p err=%d\n", xslt, err != nil);
        err = nil;
        id made = [[NSDocumentController sharedDocumentController] makeUntitledDocumentOfType:@"s2.none" error:&err];
        printf("81 %p err=%d\n", made, err != nil);
        CGFloat bottom = -1;
        [[NSView new] adjustPageHeightNew:&bottom top:0 bottom:100 limit:50];
        printf("85 %g\n", bottom);
        err = nil;
        NSString *type = [[NSDocumentController sharedDocumentController] typeForContentsOfURL:[NSURL fileURLWithPath:file] error:&err];
        printf("91 %s err=%d\n", type.UTF8String, err != nil);
        float delay = -1, interval = -1;
        [[NSCell new] getPeriodicDelay:&delay interval:&interval];
        printf("93 %g %g\n", delay, interval);
        NSString *before = @"unset", *after = @"unset";
        [[NSTextView new] smartInsertForString:@"x" replacingRange:NSMakeRange(0, 0) beforeString:&before afterString:&after];
        printf("95 before=%s after=%s\n", before.UTF8String, after.UTF8String);
        NSAttributedString *html = [[NSAttributedString alloc] initWithHTML:[@"<p>hi</p>" dataUsingEncoding:4] documentAttributes:NULL];
        printf("78 [%s]\n", html.string.UTF8String);
        [[NSFileManager defaultManager] removeItemAtPath:file error:NULL];
    }
    return 0;
}
