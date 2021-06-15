{
  description = "Best Practices CSV Report Generator";

  inputs = {
    unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
    stable.url = "github:NixOS/nixpkgs/nixos-20.09";
  };

  outputs = inputs:
    let
      system = "x86_64-linux";
      pkgs = inputs.unstable.legacyPackages.${system};
      env = pkgs.poetry2nix.mkPoetryEnv {
        projectDir = ./.;
        python = pkgs.python38;
      };
    in {
      devShell."${system}" = pkgs.mkShell {
        buildInputs = with pkgs; [
          env
          poetry
          python38Packages.pandas
        ];
        shellHook = ''
          mkdir -p .vscode
          echo '{"python.pythonPath": "${env}/bin/python", "python.formatting.provider": "black", "python.formatting.blackPath": "${env}/bin/black", "coc.preferences.formatOnSaveFiletypes":["python"]}' > .vscode/settings.json
        '';
      };
    };
}
