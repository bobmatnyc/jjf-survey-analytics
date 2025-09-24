#!/usr/bin/env node

/**
 * Session End Rule - Create Work Log
 * Creates a detailed markdown work log in docs/work-logs/
 * with timestamp, summary, and detailed work done
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function ensureWorkLogsDirectory() {
    const workLogsDir = path.join(process.cwd(), 'docs', 'work-logs');

    if (!fs.existsSync(workLogsDir)) {
        console.log('📁 Creating work-logs directory...');
        fs.mkdirSync(workLogsDir, { recursive: true });
        console.log('✅ Work-logs directory created at docs/work-logs/');
        return true; // Directory was created
    }
    return false; // Directory already existed
}

function generateTimestamp() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    return `${year}${month}${day}-${hours}${minutes}${seconds}`;
}

function getGitCommitsSinceLastLog() {
    try {
        // Get the last work log to find when it was created
        const workLogsDir = path.join(process.cwd(), 'docs', 'work-logs');

        if (!fs.existsSync(workLogsDir)) {
            // Ensure directory exists for future use
            ensureWorkLogsDirectory();
            // If no work logs directory, get recent commits
            const commits = execSync('git log --oneline -10', { encoding: 'utf8' });
            return commits.trim().split('\n');
        }
        
        const files = fs.readdirSync(workLogsDir)
            .filter(file => file.startsWith('work-log-') && file.endsWith('.md'))
            .sort()
            .reverse();
        
        if (files.length === 0) {
            // No previous logs, get recent commits
            const commits = execSync('git log --oneline -10', { encoding: 'utf8' });
            return commits.trim().split('\n');
        }
        
        // Get commits since the last log was created
        const lastLogFile = files[0];
        const lastLogPath = path.join(workLogsDir, lastLogFile);
        const lastLogStat = fs.statSync(lastLogPath);
        const lastLogTime = lastLogStat.mtime.toISOString();
        
        const commits = execSync(`git log --oneline --since="${lastLogTime}"`, { encoding: 'utf8' });
        return commits.trim() ? commits.trim().split('\n') : [];
        
    } catch (error) {
        console.error('Warning: Could not get git commits:', error.message);
        return [];
    }
}

function getCurrentProjectStatus() {
    try {
        // Check if infrastructure is running
        const dockerStatus = execSync('ssh espocrm-server "docker ps --format \\"table {{.Names}}\\t{{.Status}}\\"" 2>/dev/null || echo "SSH connection failed"', { encoding: 'utf8' });
        
        // Check website status
        const websiteStatus = execSync('curl -I https://luxurytravelclubs.app 2>/dev/null | head -1 || echo "Website check failed"', { encoding: 'utf8' });
        
        return {
            docker: dockerStatus.trim(),
            website: websiteStatus.trim()
        };
    } catch (error) {
        return {
            docker: 'Status check failed',
            website: 'Status check failed'
        };
    }
}

function createWorkLog(sessionSummary, workDetails, nextSteps) {
    const timestamp = generateTimestamp();
    const filename = `work-log-${timestamp}.md`;
    const workLogsDir = path.join(process.cwd(), 'docs', 'work-logs');
    const filePath = path.join(workLogsDir, filename);

    // Ensure directory exists
    ensureWorkLogsDirectory();
    
    const now = new Date();
    const dateString = now.toLocaleString();
    const commits = getGitCommitsSinceLastLog();
    const status = getCurrentProjectStatus();
    
    const workLogContent = `# Work Log - ${dateString}

## Session Information
- **Date**: ${dateString}
- **Timestamp**: ${timestamp}
- **Duration**: [Manual entry - estimate session length]
- **Focus Area**: [Manual entry - main area of work]

## Session Summary
${sessionSummary || '[Manual entry - brief summary of what was accomplished]'}

## Work Completed

### Major Accomplishments
${workDetails?.major || '[Manual entry - list major accomplishments]'}

### Technical Changes
${workDetails?.technical || '[Manual entry - technical changes made]'}

### Documentation Updates
${workDetails?.documentation || '[Manual entry - documentation changes]'}

### Bug Fixes / Issues Resolved
${workDetails?.bugFixes || '[Manual entry - issues resolved]'}

## Git Commits This Session
${commits.length > 0 ? commits.map(commit => `- ${commit}`).join('\n') : '- No commits found or git history unavailable'}

## Infrastructure Status
### Docker Services
\`\`\`
${status.docker}
\`\`\`

### Website Status
\`\`\`
${status.website}
\`\`\`

## Tasks and Progress
${workDetails?.tasks || '[Manual entry - Tasks worked on and progress made]'}

## Files Modified
${workDetails?.filesModified || '[Manual entry - key files created/modified]'}

## Testing Performed
${workDetails?.testing || '[Manual entry - testing done]'}

## Issues Encountered
${workDetails?.issues || '[Manual entry - problems encountered and solutions]'}

## Next Steps
${nextSteps || `[Manual entry - what should be done next session]

### Immediate Priorities
- [ ] [Task 1]
- [ ] [Task 2]
- [ ] [Task 3]

### Medium Term Goals
- [ ] [Goal 1]
- [ ] [Goal 2]

### Notes for Next Session
- [Important notes or context for next session]`}

## Session Notes
${workDetails?.notes || '[Manual entry - additional notes, observations, or context]'}

## Resources Used
- **Documentation**: [Links to docs referenced]
- **External Resources**: [External links or resources used]
- **Commands Executed**: [Key commands run during session]

---

**Session End**: ${dateString}  
**Log File**: \`${filename}\`  
**Project Status**: ${status.website.includes('200') ? '✅ Operational' : '⚠️ Check Required'}
`;

    try {
        fs.writeFileSync(filePath, workLogContent, 'utf8');
        return { success: true, filename, filePath };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

function displaySessionEnd(sessionSummary, workDetails, nextSteps) {
    console.log('🏁 SESSION END - CREATING WORK LOG');
    console.log('==================================');
    console.log('');
    
    const result = createWorkLog(sessionSummary, workDetails, nextSteps);
    
    if (result.success) {
        console.log('✅ WORK LOG CREATED SUCCESSFULLY');
        console.log(`📄 File: ${result.filename}`);
        console.log(`📍 Path: ${result.filePath}`);
        console.log('');
        
        console.log('📋 WORK LOG CONTENTS:');
        console.log('• Session information and timestamp');
        console.log('• Summary of work completed');
        console.log('• Git commits from this session');
        console.log('• Current infrastructure status');
        console.log('• Linear tasks updated');
        console.log('• Files modified');
        console.log('• Issues encountered and resolved');
        console.log('• Next steps for future sessions');
        console.log('');
        
        console.log('📝 MANUAL COMPLETION REQUIRED:');
        console.log('The work log template has been created with automatic data.');
        console.log('Please edit the file to add specific details:');
        console.log(`• Session duration and focus area`);
        console.log(`• Detailed work accomplishments`);
        console.log(`• Tasks and progress made`);
        console.log(`• Files modified`);
        console.log(`• Testing performed`);
        console.log(`• Issues encountered`);
        console.log(`• Specific next steps`);
        console.log('');
        
        console.log(`📖 EDIT WORK LOG: ${result.filePath}`);
        console.log('');
        
    } else {
        console.log('❌ FAILED TO CREATE WORK LOG');
        console.log(`Error: ${result.error}`);
        console.log('');
        console.log('📋 MANUAL WORK LOG CREATION:');
        console.log('Please manually create a work log in docs/work-logs/');
        console.log(`Suggested filename: work-log-${generateTimestamp()}.md`);
        console.log('');
    }
    
    console.log('🎯 SESSION COMPLETE');
    console.log('Remember to:');
    console.log('1. Complete the work log with specific details');
    console.log('2. Update project documentation if needed');
    console.log('3. Commit any remaining changes');
    console.log('4. Note any important context for next session');
    console.log('');
}

// Command line interface
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        // Interactive mode - create template
        displaySessionEnd();
    } else {
        // Command line arguments
        const sessionSummary = args[0];
        const nextSteps = args[1];
        displaySessionEnd(sessionSummary, {}, nextSteps);
    }
}

module.exports = {
    createWorkLog,
    displaySessionEnd,
    generateTimestamp,
    getGitCommitsSinceLastLog,
    getCurrentProjectStatus
};
