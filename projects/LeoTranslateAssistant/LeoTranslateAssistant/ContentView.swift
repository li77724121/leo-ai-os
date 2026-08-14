import SwiftUI

struct ContentView: View {
    @State private var inputText = ""
    @State private var translatedText = ""
    @State private var isLoading = false
    @State private var statusMessage = ""
    @State private var selectedProvider = TranslationProvider.openrouter
    @State private var showSettings = false

    var body: some View {
        VStack(spacing: 14) {
            // Title
            HStack {
                Image(systemName: "character.book.closed.fill")
                    .foregroundColor(.blue)
                Text("Leo AI 翻译助手")
                    .font(.title2)
                    .fontWeight(.bold)
                Spacer()
                Button(action: { showSettings.toggle() }) {
                    Image(systemName: "gearshape")
                }
                .buttonStyle(.borderless)
            }

            Divider()

            // Input
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("英文 / 外文")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    Button("粘贴") {
                        inputText = NSPasteboard.general.string(forType: .string) ?? ""
                    }
                    .buttonStyle(.borderless)
                    .font(.caption)
                }
                TextEditor(text: $inputText)
                    .font(.body)
                    .frame(height: 100)
                    .padding(6)
                    .background(Color(nsColor: .textBackgroundColor))
                    .cornerRadius(8)
            }

            // Translate button
            HStack {
                Picker("", selection: $selectedProvider) {
                    ForEach(TranslationProvider.allCases, id: \.self) { p in
                        Text(p.rawValue).tag(p)
                    }
                }
                .frame(width: 140)

                Spacer()

                Button(action: translate) {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .scaleEffect(0.7)
                                .frame(width: 16, height: 16)
                        }
                        Text(isLoading ? "翻译中..." : "翻译 → 中文")
                    }
                    .frame(minWidth: 120)
                }
                .buttonStyle(.borderedProminent)
                .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty || isLoading)
            }

            // Result
            VStack(alignment: .leading, spacing: 4) {
                Text("中文翻译")
                    .font(.caption)
                    .foregroundColor(.secondary)
                ScrollView {
                    Text(translatedText.isEmpty ? "翻译结果将显示在这里..." : translatedText)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(8)
                }
                .frame(height: 80)
                .background(Color(nsColor: .textBackgroundColor))
                .cornerRadius(8)
            }

            if !statusMessage.isEmpty {
                Text(statusMessage)
                    .font(.caption)
                    .foregroundColor(statusMessage.contains("❌") ? .red : .green)
            }

            // Action buttons
            HStack {
                Button("复制结果") {
                    if !translatedText.isEmpty {
                        NSPasteboard.general.clearContents()
                        NSPasteboard.general.setString(translatedText, forType: .string)
                        statusMessage = "✅ 已复制"
                    }
                }
                .buttonStyle(.bordered)
                .disabled(translatedText.isEmpty)

                Spacer()

                Button("清空") {
                    inputText = ""
                    translatedText = ""
                    statusMessage = ""
                }
                .buttonStyle(.bordered)
            }
        }
        .padding()
        .frame(width: 460, height: 460)
        .sheet(isPresented: $showSettings) {
            SettingsView()
        }
    }

    func translate() {
        guard !inputText.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        isLoading = true
        statusMessage = ""
        translatedText = ""

        TranslationService.shared.translate(text: inputText, provider: selectedProvider) { result in
            DispatchQueue.main.async {
                isLoading = false
                if let text = result {
                    translatedText = text
                    statusMessage = "✅ 翻译完成"
                } else {
                    statusMessage = "❌ 翻译失败，请检查API密钥"
                }
            }
        }
    }
}
