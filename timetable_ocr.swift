import Foundation
import Vision
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false
try VNImageRequestHandler(url: url).perform([req])
let rows = (req.results ?? []).compactMap { ob -> [String: Any]? in
 guard let text = ob.topCandidates(1).first?.string else { return nil }
 return ["text": text, "x": ob.boundingBox.midX, "y": 1-ob.boundingBox.midY]
}
let data = try JSONSerialization.data(withJSONObject: rows)
print(String(data: data, encoding: .utf8)!)
