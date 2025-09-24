#!/usr/bin/env node

/**
 * Session Start Rule - Check Previous Work Logs
 * Automatically checks docs/work-logs/ for the most recent session
 * and provides a summary of what was done last time
 */

const fs = require('fs');
const path = require('path');

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

function getLastWorkLog() {
    const workLogsDir = path.join(process.cwd(), 'docs', 'work-logs');

    try {
        // Ensure work-logs directory exists
        const directoryCreated = ensureWorkLogsDirectory();
        if (directoryCreated) {
            return null; // No previous logs if directory was just created
        }
        
        // Get all work log files
        const files = fs.readdirSync(workLogsDir)
            .filter(file => file.startsWith('work-log-') && file.endsWith('.md'))
            .sort()
            .reverse(); // Most recent first
        
        if (files.length === 0) {
            console.log('📋 No previous work logs found');
            return null;
        }
        
        const lastLogFile = files[0];
        const lastLogPath = path.join(workLogsDir, lastLogFile);
        const lastLogContent = fs.readFileSync(lastLogPath, 'utf8');
        
        return {
            filename: lastLogFile,
            path: lastLogPath,
            content: lastLogContent
        };
        
    } catch (error) {
        console.error('❌ Error reading work logs:', error.message);
        return null;
    }
}

function extractSummaryFromLog(content) {
    // Extract key sections from the work log
    const lines = content.split('\n');
    let summary = '';
    let inSummary = false;
    let inNextSteps = false;
    let nextSteps = '';
    
    for (const line of lines) {
        if (line.includes('## Session Summary') || line.includes('## Summary')) {
            inSummary = true;
            continue;
        }
        if (line.includes('## Next Steps') || line.includes('## Next Session')) {
            inSummary = false;
            inNextSteps = true;
            continue;
        }
        if (line.startsWith('## ') && inSummary) {
            inSummary = false;
        }
        if (line.startsWith('## ') && inNextSteps) {
            inNextSteps = false;
        }
        
        if (inSummary && line.trim()) {
            summary += line + '\n';
        }
        if (inNextSteps && line.trim()) {
            nextSteps += line + '\n';
        }
    }
    
    return { summary: summary.trim(), nextSteps: nextSteps.trim() };
}

function displaySessionStart() {
    console.log('🚀 SESSION START - CHECKING PREVIOUS WORK');
    console.log('=========================================');
    console.log('');
    
    const lastLog = getLastWorkLog();
    
    if (!lastLog) {
        console.log('📋 FIRST SESSION OR NO PREVIOUS LOGS');
        console.log('• Starting fresh session');
        console.log('• Work log will be created at session end');
        console.log('• Check docs/PROGRESS.md for project status');
        console.log('');
        console.log('🎯 RECOMMENDED STARTUP ACTIONS:');
        console.log('1. Verify infrastructure: ssh espocrm-server "docker ps"');
        console.log('2. Check website status: curl -I https://luxurytravelclubs.app');
        console.log('3. Review progress: docs/PROGRESS.md');
        console.log('4. Continue with planned work from previous session');
        console.log('');
        return;
    }
    
    // Extract timestamp from filename
    const timestamp = lastLog.filename.replace('work-log-', '').replace('.md', '');
    const date = new Date(timestamp.replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/, '$1-$2-$3T$4:$5:$6'));
    
    console.log(`📋 LAST SESSION: ${date.toLocaleString()}`);
    console.log(`📄 Log File: ${lastLog.filename}`);
    console.log('');
    
    const { summary, nextSteps } = extractSummaryFromLog(lastLog.content);
    
    if (summary) {
        console.log('📊 LAST SESSION SUMMARY:');
        console.log('========================');
        console.log(summary);
        console.log('');
    }
    
    if (nextSteps) {
        console.log('🎯 PLANNED NEXT STEPS:');
        console.log('======================');
        console.log(nextSteps);
        console.log('');
    }
    
    console.log('🔍 RECOMMENDED STARTUP ACTIONS:');
    console.log('1. Verify infrastructure: ssh espocrm-server "docker ps"');
    console.log('2. Check website status: curl -I https://luxurytravelclubs.app');
    console.log('3. Review current progress: docs/PROGRESS.md');
    console.log('4. Continue from planned next steps above');
    console.log('');
    
    console.log(`📖 FULL LAST SESSION LOG: ${lastLog.path}`);
    console.log('');
}

// Run the session start check
if (require.main === module) {
    displaySessionStart();
}

module.exports = {
    getLastWorkLog,
    extractSummaryFromLog,
    displaySessionStart
};
