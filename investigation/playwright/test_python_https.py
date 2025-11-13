#!/usr/bin/env python3
"""
ネットワークアクセステスト - Python HTTP/HTTPSライブラリ編
"""
import urllib.request
import urllib.error
import socket

def test_urllib(url, name):
    """urllib でテスト"""
    print(f"\n{'='*60}")
    print(f"Testing with urllib: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            content_length = len(response.read())
            print(f"✅ SUCCESS")
            print(f"   Status: {status}")
            print(f"   Content-Length: {content_length} bytes")
            return True
    except urllib.error.URLError as e:
        print(f"❌ FAILED (URLError)")
        print(f"   Reason: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ FAILED")
        print(f"   Error: {type(e).__name__}: {str(e)[:200]}")
        return False

def test_socket(host, port, name):
    """socket でTCP接続をテスト"""
    print(f"\n{'='*60}")
    print(f"Testing socket connection: {name}")
    print(f"Host: {host}:{port}")
    print(f"{'='*60}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        print(f"✅ SUCCESS - TCP connection established")
        sock.close()
        return True
    except socket.timeout:
        print(f"❌ FAILED - Connection timeout")
        return False
    except socket.error as e:
        print(f"❌ FAILED - Socket error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED - {type(e).__name__}: {str(e)}")
        return False

def main():
    print("="*60)
    print("Python HTTPS/Socket Network Access Test")
    print("="*60)

    # urllib テスト
    print("\n" + "="*60)
    print("URLLIB TESTS")
    print("="*60)

    urllib_results = {}
    test_urls = [
        ("https://example.com", "Example.com"),
        ("https://www.google.com", "Google"),
        ("https://api.github.com", "GitHub API"),
        ("https://httpbin.org/get", "HTTPBin"),
        ("https://claude.ai", "Claude.ai"),
        ("http://example.com", "Example.com (HTTP)"),
    ]

    for url, name in test_urls:
        urllib_results[name] = test_urllib(url, name)

    # Socket テスト
    print("\n" + "="*60)
    print("SOCKET TESTS")
    print("="*60)

    socket_results = {}
    socket_tests = [
        ("example.com", 80, "Example.com:80"),
        ("example.com", 443, "Example.com:443"),
        ("www.google.com", 443, "Google:443"),
        ("api.github.com", 443, "GitHub API:443"),
        ("claude.ai", 443, "Claude.ai:443"),
    ]

    for host, port, name in socket_tests:
        socket_results[name] = test_socket(host, port, name)

    # サマリー
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    print("\nURLLib Results:")
    for name, success in urllib_results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    print("\nSocket Results:")
    for name, success in socket_results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    urllib_success = sum(1 for v in urllib_results.values() if v)
    socket_success = sum(1 for v in socket_results.values() if v)

    print(f"\nTotal urllib: {urllib_success}/{len(urllib_results)} successful")
    print(f"Total socket: {socket_success}/{len(socket_results)} successful")

if __name__ == "__main__":
    main()
