import Foundation

enum TranslationProvider: String, CaseIterable {
    case openrouter = "OpenRouter (推荐)"
    case deepseek = "DeepSeek"
    case ollama = "Ollama (本地)"
}

class TranslationService {
    static let shared = TranslationService()
    private let defaults = UserDefaults.standard

    var openRouterKey: String {
        get { defaults.string(forKey: "openrouter_key") ?? "" }
        set { defaults.set(newValue, forKey: "openrouter_key") }
    }

    var deepseekKey: String {
        get { defaults.string(forKey: "deepseek_key") ?? "" }
        set { defaults.set(newValue, forKey: "deepseek_key") }
    }

    var ollamaURL: String {
        get { defaults.string(forKey: "ollama_url") ?? "http://localhost:11434" }
        set { defaults.set(newValue, forKey: "ollama_url") }
    }

    func translate(text: String, provider: TranslationProvider, completion: @escaping (String?) -> Void) {
        switch provider {
        case .openrouter:
            translateWithOpenRouter(text: text, completion: completion)
        case .deepseek:
            translateWithDeepSeek(text: text, completion: completion)
        case .ollama:
            translateWithOllama(text: text, completion: completion)
        }
    }

    private func translateWithOpenRouter(text: String, completion: @escaping (String?) -> Void) {
        guard !openRouterKey.isEmpty else {
            completion("请先在设置中配置 OpenRouter API Key\n\n获取: https://openrouter.ai/keys")
            return
        }

        let url = URL(string: "https://openrouter.ai/api/v1/chat/completions")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.addValue("Bearer \(openRouterKey)", forHTTPHeaderField: "Authorization")
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "model": "deepseek/deepseek-chat",
            "messages": [
                ["role": "system", "content": "You are a professional translator. Translate the following text to Simplified Chinese. Return ONLY the translated text, no explanations."],
                ["role": "user", "content": text]
            ]
        ]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: req) { data, _, err in
            guard let data = data, err == nil,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let choices = json["choices"] as? [[String: Any]],
                  let msg = choices.first?["message"] as? [String: Any],
                  let content = msg["content"] as? String else {
                completion(nil)
                return
            }
            completion(content.trimmingCharacters(in: .whitespacesAndNewlines))
        }.resume()
    }

    private func translateWithDeepSeek(text: String, completion: @escaping (String?) -> Void) {
        guard !deepseekKey.isEmpty else {
            completion("请先在设置中配置 DeepSeek API Key")
            return
        }

        let url = URL(string: "https://api.deepseek.com/v1/chat/completions")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.addValue("Bearer \(deepseekKey)", forHTTPHeaderField: "Authorization")
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "model": "deepseek-chat",
            "messages": [
                ["role": "system", "content": "Translate to Chinese. Return only translation."],
                ["role": "user", "content": text]
            ]
        ]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: req) { data, _, _ in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let choices = json["choices"] as? [[String: Any]],
                  let msg = choices.first?["message"] as? [String: Any],
                  let content = msg["content"] as? String else {
                completion(nil)
                return
            }
            completion(content.trimmingCharacters(in: .whitespacesAndNewlines))
        }.resume()
    }

    private func translateWithOllama(text: String, completion: @escaping (String?) -> Void) {
        let url = URL(string: "\(ollamaURL)/api/chat")!
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "model": "qwen2.5-coder:7b",
            "messages": [
                ["role": "system", "content": "Translate to Chinese. Return only translation."],
                ["role": "user", "content": text]
            ]
        ]
        req.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: req) { data, _, _ in
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let msg = json["message"] as? [String: Any],
                  let content = msg["content"] as? String else {
                completion(nil)
                return
            }
            completion(content.trimmingCharacters(in: .whitespacesAndNewlines))
        }.resume()
    }
}
