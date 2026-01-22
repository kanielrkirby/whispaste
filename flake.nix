{
  description = "whispaste - Simple voice-to-paste tool";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      defaultPackage = forAllSystems (pkgs: pkgs.python312Packages.buildPythonApplication {
        pname = "whispaste";
        version = "0.1.0";
        pyproject = true;
        src = ./.;
        propagatedBuildInputs = with pkgs.python312Packages; [
          openai
          python-dotenv
          sounddevice
          numpy
          pyperclip
        ];
        nativeBuildInputs = [ pkgs.python312Packages.setuptools ];
          buildInputs = [
            pkgs.portaudio
            pkgs.libnotify
          ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
            pkgs.wl-clipboard
            pkgs.xdotool
            pkgs.ydotool
            pkgs.wtype
          ];
        meta = {
          description = "Simple voice-to-paste tool";
          license = pkgs.lib.licenses.mit;
        };
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          buildInputs = with pkgs.python312Packages; [
            pkgs.python312
            openai
            python-dotenv
            sounddevice
            pyperclip
            setuptools
          ] ++ [
            pkgs.portaudio
            pkgs.libnotify
          ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
            pkgs.wl-clipboard
            pkgs.xdotool
            pkgs.ydotool
            pkgs.wtype
          ];
          shellHook = ''
            if [ -f .env ]; then
              set -a
              source .env
              set +a
            fi
          '';
        };
      });
    };
}
