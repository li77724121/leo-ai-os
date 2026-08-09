import Foundation

class AIService {
    static let baseURL = "http://localhost:8000"
    
    // MARK: - AI生成图片
    static func generate(_ prompt: String) async -> String {
        let url = URL(string: "\(baseURL)/generate")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = AIRequest(prompt: prompt)
        request.httpBody = try? JSONEncoder().encode(body)
        
        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            let result = try JSONDecoder().decode(AIResult.self, from: data)
            return result.url
        } catch {
            print("AI生成失败: \(error)")
            return "https://picsum.photos/1024/1024?random=\(Int.random(in: 1...1000))"
        }
    }
    
    // MARK: - AI抠图
    static func removeBackground(_ image: UIImage) async -> UIImage? {
        guard let imageData = image.jpegData(compressionQuality: 0.8) else { return nil }
        
        let url = URL(string: "\(baseURL)/cutout")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"photo.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body
        
        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            let result = try JSONDecoder().decode(CutoutResult.self, from: data)
            
            // 下载抠图结果
            if let imageURL = URL(string: result.url) {
                let (imageData, _) = try await URLSession.shared.data(from: imageURL)
                return UIImage(data: imageData)
            }
        } catch {
            print("抠图失败: \(error)")
        }
        return nil
    }
}
