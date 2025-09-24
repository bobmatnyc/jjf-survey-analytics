#!/usr/bin/env node

/**
 * Session Manager - Main Entry Point for Session Rules
 * Handles both session start and session end workflows
 */

const { displaySessionStart } = require('./session-start');
const { displaySessionEnd } = require('./session-end');

function showUsage() {
    console.log('📋 SESSION MANAGER USAGE');
    console.log('========================');
    console.log('');
    console.log('Start a new session:');
    console.log('  node .augment/rules/session-manager.js start');
    console.log('  node .augment/rules/session-start.js');
    console.log('');
    console.log('End current session:');
    console.log('  node .augment/rules/session-manager.js end');
    console.log('  node .augment/rules/session-end.js');
    console.log('');
    console.log('End session with summary:');
    console.log('  node .augment/rules/session-manager.js end "Session summary" "Next steps"');
    console.log('');
    console.log('📁 Work logs are stored in: docs/work-logs/');
    console.log('');
}

function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        showUsage();
        return;
    }
    
    const command = args[0].toLowerCase();
    
    switch (command) {
        case 'start':
        case 'begin':
        case 'startup':
            displaySessionStart();
            break;
            
        case 'end':
        case 'finish':
        case 'complete':
            const sessionSummary = args[1];
            const nextSteps = args[2];
            displaySessionEnd(sessionSummary, {}, nextSteps);
            break;
            
        case 'help':
        case '--help':
        case '-h':
            showUsage();
            break;
            
        default:
            console.log(`❌ Unknown command: ${command}`);
            console.log('');
            showUsage();
            break;
    }
}

if (require.main === module) {
    main();
}

module.exports = {
    showUsage,
    main
};
