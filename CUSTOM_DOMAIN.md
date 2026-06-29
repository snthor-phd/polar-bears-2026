# Putting the site on your own domain

GitHub Pages supports a free custom domain with automatic HTTPS. You need a
domain you own (any registrar). Two ways to point it — pick one.

---

## Option A — a subdomain (easiest, recommended)
e.g. `caravan.yourdomain.com`

1. At your registrar's DNS, add **one CNAME record**:

   | Type  | Host / Name | Value                       |
   |-------|-------------|-----------------------------|
   | CNAME | `caravan`   | `snthor-phd.github.io`      |

2. Add a file named `CNAME` (no extension) in this folder containing just the
   full domain:

   ```
   caravan.yourdomain.com
   ```

3. `./deploy.sh`  — then on github.com go to **Settings → Pages**, confirm the
   custom domain shows, and tick **Enforce HTTPS** once the certificate is issued
   (usually a few minutes, can take up to a day).

---

## Option B — a bare/apex domain
e.g. `yourdomain.com`

1. At your registrar's DNS, add these **four A records** (host `@`) pointing to
   GitHub's current Pages addresses:

   ```
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```

   (Optional, for IPv6, four AAAA records on `@`:)
   ```
   2606:50c0:8000::153
   2606:50c0:8001::153
   2606:50c0:8002::153
   2606:50c0:8003::153
   ```

2. Add a `CNAME` file in this folder containing just:
   ```
   yourdomain.com
   ```

3. `./deploy.sh`, then **Settings → Pages** → confirm + **Enforce HTTPS**.

> GitHub validates the domain and shows a green check on the Pages settings page
> once DNS has propagated. If it complains, give DNS time and re-check there —
> that page is the source of truth and lists the exact values it expects.

---

### Notes
- The `github.io` URL keeps working even after you add a custom domain.
- Don't commit a `CNAME` file with a placeholder domain — Pages will try to use
  it and break. Only add it once you have a real domain.
- Tell me the domain and I'll drop the `CNAME` file in and re-deploy for you.
