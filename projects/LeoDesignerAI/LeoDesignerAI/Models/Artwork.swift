import Foundation

struct Artwork: Identifiable, Codable {
    let id: UUID
    var prompt: String
    var imageURL: String?
    var date: Date
    var category: ArtworkCategory = .aiGenerated
}

enum ArtworkCategory: String, Codable, CaseIterable {
    case aiGenerated = "AI生成"
    case cutout = "抠图"
    case background = "换背景"
    case template = "模板"
}
