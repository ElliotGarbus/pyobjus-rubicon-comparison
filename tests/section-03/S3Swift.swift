// F7: Swift code reached through @objc, the way an app's shim exposes it.
import Foundation

public enum NotebookError: Error {
    case noSuchNote
}

@objc(S3Notebook)
public final class Notebook: NSObject {
    @objc public let title: String
    @objc public var author = "anonymous"
    @objc public private(set) var notes: [String] = []

    @objc(initWithTitle:)
    public init(title: String) {
        self.title = title
        super.init()
    }

    @objc(addNote:)
    public func add(_ text: String) -> Int {
        notes.append(text)
        return notes.count
    }

    @objc public func squares() -> [Int] { [0, 1, 4, 9] }
    @objc public func ratio() -> Double { 0.25 }
    @objc public func isReady() -> Bool { true }
    @objc public func missing() -> String? { nil }

    @objc public func summary() -> [String: Any] {
        ["count": 2, "isEmpty": false, "nested": ["a": [1, 2]]]
    }

    @objc(countOf:)
    public func count(of items: [String]) -> Int { items.count }

    // Returns the value for key as text, or "absent".
    @objc(valueIn:forKey:)
    public func value(in options: [String: Any], forKey key: String) -> String {
        options[key].map { "\($0)" } ?? "absent"
    }

    @objc(noteAtIndex:error:)
    public func note(at index: Int) throws -> String {
        guard notes.indices.contains(index) else { throw NotebookError.noSuchNote }
        return notes[index]
    }

    @objc(greetingWithCompletionHandler:)
    public func greeting() async -> String {
        try? await Task.sleep(nanoseconds: 50_000_000)
        return "hello"
    }

    @objc(failingGreetingWithCompletionHandler:)
    public func failingGreeting() async throws -> String {
        throw NotebookError.noSuchNote
    }
}

// No explicit Objective-C name, so Swift generates one.
public final class Unnamed: NSObject {
    @objc public func ping() -> Int { 7 }
}

@objc(S3MetronomeDelegate)
public protocol MetronomeDelegate: NSObjectProtocol {
    @objc(metronome:didTick:)
    func metronome(_ metronome: Metronome, didTick count: Int)

    @objc(metronome:shouldContinueAfter:)
    optional func metronome(_ metronome: Metronome, shouldContinueAfter count: Int) -> Bool

    @objc(metronome:scaleFor:)
    optional func metronome(_ metronome: Metronome, scaleFor count: Int) -> Int

    @objc(metronome:labelFor:)
    optional func metronome(_ metronome: Metronome, labelFor count: Int) -> String?
}

@objc(S3Metronome)
public final class Metronome: NSObject {
    @objc public weak var delegate: MetronomeDelegate?
    @objc public private(set) var ticks = 0
    @objc public private(set) var continueAnswers: [Bool] = []
    @objc public private(set) var scales: [Int] = []
    @objc public private(set) var labels: [String] = []
    @objc public private(set) var tickedOnMainThread = false

    // Calls each delegate method once per tick, on the calling thread.
    @objc(runTicks:)
    public func run(ticks count: Int) {
        guard let delegate else { return }
        for i in 1...count {
            ticks = i
            tickedOnMainThread = Thread.isMainThread
            delegate.metronome(self, didTick: i)
            if let answer = delegate.metronome?(self, shouldContinueAfter: i) {
                continueAnswers.append(answer)
            }
            if let scale = delegate.metronome?(self, scaleFor: i) {
                scales.append(scale)
            }
            if let label = delegate.metronome?(self, labelFor: i) {
                labels.append(label)
            }
        }
    }

    @objc public private(set) var finished = false

    // The same calls on a thread Swift creates. It returns at once, without
    // waiting, so the caller polls `finished`. Section 2 covers a call that
    // waits on a callback from another thread.
    @objc(startTicksOnBackgroundThread:)
    public func startOnBackground(ticks count: Int) {
        finished = false
        Thread { [self] in
            run(ticks: count)
            finished = true
        }.start()
    }
}
