

## AI Usage Declaration

AI tools were used during the development of this project as productivity and learning aids. They assisted with debugging, code review, documentation drafting, and troubleshooting specific implementation issues.

All major implementation decisions, testing, integration work, deployment, and final code validation were performed manually.

---

# AI Tools Used

## ChatGPT

Used for:

* Debugging assistance
* Explaining framework behavior
* Reviewing implementation approaches
* Documentation drafting

## Claude

Used for:

* Repository analysis
* Reviewing project structure
* Suggesting implementation improvements
* Troubleshooting deployment issues

---

# How AI Assisted

AI was used similarly to how a developer might use documentation, Stack Overflow, or an online assistant.

Examples include:

* Reviewing Flask configuration issues
* Debugging React routing problems
* Understanding deployment requirements for Render and Vercel
* Drafting documentation templates
* Suggesting improvements to project structure

All generated suggestions were reviewed and tested before being incorporated into the project.

---

# Example Prompts

### Frontend Debugging

```text
Help identify why the React application is showing a blank screen after routing changes.
```

### Backend Configuration

```text
Review the Flask startup configuration and identify possible deployment issues.
```

### Deployment

```text
Verify Render and Vercel deployment settings for a Flask backend and React frontend.
```

### Documentation

```text
Help structure project documentation and setup instructions.
```

---

# Examples of Incorrect AI Suggestions

## Example 1: React Routing Issue

A suggested routing change introduced rendering problems that resulted in a blank screen.

### How It Was Detected

* Browser console errors appeared
* Application failed to render correctly

### Resolution

The routing configuration was reviewed manually and corrected. The application was rebuilt and verified before proceeding.

---

## Example 2: Backend Startup Configuration

An early suggestion did not properly account for deployment environment requirements.

### How It Was Detected

The application failed to start correctly during deployment testing.

### Resolution

The startup configuration was adjusted and tested locally before redeploying.

---

## Example 3: File Path Recommendations

Some generated commands referenced incorrect project paths.

### How It Was Detected

Commands failed during execution due to missing directories.

### Resolution

Repository structure was verified manually and commands were updated to match the actual project layout.

---

# Verification Process

For each significant change:

1. Code was reviewed manually.
2. Backend tests were executed.
3. Importer tests were executed.
4. Frontend builds were verified.
5. Features were tested locally.
6. Deployment was validated after publishing.

No AI-generated code was accepted without testing and verification.

---

# Conclusion

AI was used as a development assistant to improve productivity and help troubleshoot issues. Final implementation decisions, integration work, testing, debugging, and deployment verification were completed manually.
