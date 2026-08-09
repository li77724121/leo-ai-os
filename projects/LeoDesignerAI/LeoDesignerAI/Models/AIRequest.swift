import Foundation

struct AIRequest: Codable {
    let prompt: String
    let model: String = "flux"
    let size: String = "1024x1024"
}

struct AIResult: Codable {
    let url: String
    let id: String?
}

struct CutoutRequest: Codable {
    let image: Data
}

struct CutoutResult: Codable {
    let url: String
    let id: String
}
