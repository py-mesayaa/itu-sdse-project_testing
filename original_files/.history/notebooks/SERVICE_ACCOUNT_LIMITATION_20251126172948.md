# Service Account Storage Quota Limitation

## Issue

Service accounts **cannot upload files** to regular Google Drive folders due to Google's storage quota restrictions. They can only:
- ✅ Read/download files (pull works)
- ❌ Upload files (push fails with quota error)

## Solutions

### Option 1: Use Google Workspace Shared Drive (Recommended)

If you have Google Workspace, use a **Shared Drive** instead of a regular folder:

1. Create a Shared Drive in Google Workspace
2. Share it with the service account email
3. Get the Shared Drive ID (from the URL)
4. Update DVC config:
   ```bash
   dvc remote modify gdrive url gdrive://SHARED_DRIVE_ID
   ```

**Note:** Regular Google accounts cannot create Shared Drives - you need Google Workspace.

### Option 2: Use OAuth with Custom Google Cloud Project

Set up your own OAuth app to avoid the "blocked app" issue:

1. Create a Google Cloud Project
2. Enable Google Drive API
3. Create OAuth 2.0 credentials
4. Configure DVC to use your OAuth app

This allows each user to authenticate with their own Google account.

### Option 3: Use Alternative Storage

Consider using:
- **GitHub LFS** (if data is < 100MB per file)
- **AWS S3** (free tier available)
- **Azure Blob Storage**
- **Google Cloud Storage** (different from Drive)

### Option 4: Manual Upload Workaround

For now, you can:
1. Use `dvc pull` to download data (this works!)
2. Manually upload files to Google Drive when needed
3. Or use the GitHub remote as a backup

## Current Status

- ✅ **Pull works** - Team members can download data
- ❌ **Push fails** - Cannot upload via service account

## Testing Pull

You can test that pulling works:

```bash
cd notebooks
# Remove local cache to test
rm -rf .dvc/cache
dvc pull
```

This should successfully download data from Google Drive.

## Recommendation

For a team setup where everyone needs to push/pull:
1. **Best:** Use Google Workspace Shared Drive
2. **Alternative:** Set up OAuth with custom Google Cloud project
3. **Quick fix:** Use GitHub remote for pushing, Google Drive for pulling

