import SwiftUI

struct SettingsView: View {
    @State private var serverURL = "http://localhost:8000"
    @State private var apiKey = ""
    
    var body: some View {
        NavigationStack {
            Form {
                Section("服务器配置") {
                    TextField("后端地址", text: $serverURL)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                    
                    SecureField("API Key (可选)", text: $apiKey)
                        .autocapitalization(.none)
                        .disableAutocorrection(true)
                }
                
                Section("关于") {
                    HStack {
                        Text("版本")
                        Spacer()
                        Text("v1.0 MVP")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("框架")
                        Spacer()
                        Text("SwiftUI + FastAPI")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Text("AI引擎")
                        Spacer()
                        Text("OpenAI / Flux")
                            .foregroundColor(.secondary)
                    }
                    
                    Link("Hermes 自动开发", destination: URL(string: "https://hermes.nousresearch.com")!)
                }
                
                Section {
                    Button("清除所有缓存", role: .destructive) {
                        // TODO: 清除缓存
                    }
                }
            }
            .navigationTitle("设置")
        }
    }
}

#Preview {
    SettingsView()
}
