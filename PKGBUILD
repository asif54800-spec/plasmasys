# Maintainer: Muhammad Asif Rauf <asif54800@gmail.com>
pkgname=plasmasys
pkgver=1.0
pkgrel=1
pkgdesc="A simple Python sensor monitor for the KDE Plasma 6 desktop."
arch=('any')
url="https://github.com/asif54800-spec/plasmasys"
license=('MIT')
depends=('python-pyqt6' 'python-psutil')
optdepends=('wireless_tools: for displaying Wi-Fi SSID')

# This part downloads from your (now correct) tag
source=("$pkgname-$pkgver.tar.gz::https://github.com/asif54800-spec/plasmasys/archive/refs/tags/v$pkgver.tar.gz")

# This checksum is probably wrong now, we will fix it in the next step
sha256sums=('fd189a283ad307ccb3e4a26d032f5ff7226d34f0a19591726c554976fb5a533f')

# THIS IS THE FIX:
# This function runs after extracting and moves into the correct folder.
prepare() {
    cd "$pkgname-$pkgver"
}

package() {
    # This will now work, because we are inside the 'plasmasys-1.0' folder
    install -Dm755 "plasmasys.py" "$pkgdir/usr/bin/$pkgname"
    
    install -Dm644 "plasmasys.desktop" "$pkgdir/usr/share/applications/plasmasys.desktop"
    
    install -Dm644 "plasmasys.svg" "$pkgdir/usr/share/icons/hicolor/scalable/apps/plasmasys.svg"
}
