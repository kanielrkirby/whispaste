class Whispaste < Formula
  include Language::Python::Virtualenv

  desc "Simple voice-to-paste tool using OpenAI Whisper"
  homepage "https://github.com/kanielrkirby/whispaste"
  url "https://github.com/kanielrkirby/whispaste/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "" # Will be filled by CI
  license "MIT"
  head "https://github.com/kanielrkirby/whispaste.git", branch: "main"

  depends_on "python@3.12"
  depends_on "portaudio"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_predicate bin/"whispaste", :exist?
  end
end
