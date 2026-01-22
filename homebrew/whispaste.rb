class Whispaste < Formula
  desc "Simple voice-to-paste tool using OpenAI Whisper"
  homepage "https://github.com/kanielrkirby/whispaste"
  url "https://files.pythonhosted.org/packages/py3/w/whispaste/whispaste-0.1.0-py3-none-any.whl"
  sha256 "" # Fill in after building wheel
  license "MIT"
  head "https://github.com/kanielrkirby/whispaste.git", branch: "main"

  depends_on "python@3.12"
  depends_on "portaudio"
  depends_on "libnotify"
  depends_on "xdotool" if OS.linux?

  def install
    # Install via pip to libexec
    system "pip3", "install", *std_pip_args(build_isolation: false), "--prefix=#{libexec}", "whispaste"

    # Create wrapper for XDG config support
    (libexec/"bin").mkpath
    (libexec/"bin/whispaste").write <<~EOS
      #!/bin/bash
      export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
      exec python "#{libexec}/lib/python3.12/site-packages/whispaste.py" "$@"
    EOS

    bin.install_symlink libexec/"bin/whispaste"
  end

  test do
    assert_match "whispaste", pipe_output("#{bin}/whispaste", "\x04")
  end
end
