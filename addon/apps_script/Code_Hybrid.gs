/**
 * Gmail Email Organizer Add-on - GEMINI-POWERED VERSION
 *
 * Architecture:
 * - Gemini API → Priority classification + To-do extraction + Email summary
 * - Apps Script → Smart caching + UI
 * - Displays:
 *   1. Email Summary: All emails with priority, summary, task count, sender
 *   2. To-Do List: Actionable tasks with links to source emails
 *
 */

// ========== CONFIGURATION ==========
const GEMINI_API_KEY = '';      // From https://makersuite.google.com
// ===================================

/**
 * Called when message is opened in Gmail
 */
function onGmailMessageOpen(e) {
  try {
    Logger.log('\n=== onGmailMessageOpen called ===');

    // Check if event object exists (for testing vs production)
    if (!e || !e.gmail) {
      Logger.log('✗ Error: Event object missing or invalid');
      Logger.log('Event object: ' + JSON.stringify(e));
      return buildErrorCard('Please open this add-on from an actual Gmail message.\n\nDeploy as "Test deployment" and open in Gmail to test.');
    }

    // Get email details from event object
    const accessToken = e.gmail.accessToken;
    const messageId = e.gmail.messageId;

    Logger.log('Message ID: ' + messageId);

    // Fetch email details
    let email;
    try {
      email = getEmailDetails(messageId, accessToken);
      Logger.log('✓ Email fetched: "' + email.subject + '"');
    } catch (fetchError) {
      Logger.log('✗ Error fetching email details: ' + fetchError);
      Logger.log('Stack trace: ' + fetchError.stack);
      throw fetchError;
    }

    // Process with hybrid approach
    let result;
    try {
      result = processEmailHybrid(email);
      Logger.log('✓ Processing complete. Priority: ' + result.priority);
    } catch (processError) {
      Logger.log('✗ Error processing email: ' + processError);
      Logger.log('Stack trace: ' + processError.stack);
      throw processError;
    }

    // Build card to display results
    return buildResultCard(result);

  } catch (error) {
    Logger.log('\n✗✗✗ CRITICAL ERROR in onGmailMessageOpen ✗✗✗');
    Logger.log('Error: ' + error.toString());
    Logger.log('Error name: ' + error.name);
    Logger.log('Error message: ' + error.message);
    Logger.log('Error stack: ' + error.stack);
    return buildErrorCard('Error: ' + error.toString() + '\n\nCheck View > Logs for details.');
  }
}

/**
 * Called when homepage is opened - Auto-analyze emails
 */
function onHomepage(e) {
  Logger.log('\n=== onHomepage called - Auto-analyzing emails ===');

  // Automatically run analysis and show results
  return showEmailList(e, 'priority');
}

/**
 * Show email list with sorting options
 */
function showEmailList(e, sortBy) {
  try {
    Logger.log(`\n=== showEmailList called (sortBy: ${sortBy}) ===`);

    // Auto-analyze emails from last 24 hours
    const emails = fetchRecentEmails(24);
    Logger.log(`✓ Found ${emails.length} emails`);

    if (emails.length === 0) {
      return buildInfoCard('No emails found in the last 24 hours');
    }

    // Process emails and collect results
    const results = [];
    const emailSummaries = []; // Track all emails with their analysis
    // STRATEGY 5: Increase batch size to 50 emails for speed testing
    const MAX_NEW_EMAILS = 50; // Test parallel processing performance
    let newEmailsProcessed = 0;

    // STRATEGY 3: Batch cache lookups - collect all email IDs first
    const emailIds = emails.map(e => e.id);
    const cacheResults = batchGetCachedResults(emailIds);

    // Separate cached and uncached emails
    const cachedEmails = [];
    const uncachedEmails = [];

    for (let i = 0; i < emails.length; i++) {
      const email = emails[i];
      const cached = cacheResults[email.id];

      if (cached) {
        Logger.log(`Email ${i + 1}: Using cached result`);
        cachedEmails.push({ email, cached });
      } else {
        uncachedEmails.push(email);
      }
    }

    // Add all cached results first
    cachedEmails.forEach(({ email, cached }) => {
      results.push(cached);
      emailSummaries.push({
        subject: cached.subject,
        sender: email.sender,
        priority: cached.priority,
        summary: cached.summary || cached.subject,
        timestamp: email.timestamp,
        id: email.id
      });
    });

    // Limit uncached emails to process
    const emailsToProcess = uncachedEmails.slice(0, MAX_NEW_EMAILS);
    Logger.log(`Processing ${emailsToProcess.length} new emails (${cachedEmails.length} from cache)`);

    // STRATEGY 2: Parallel Gemini API calls using UrlFetchApp.fetchAll()
    // First, quick pre-check all emails to see which need Gemini
    const emailsNeedingGemini = [];
    const emailsSkippingGemini = [];

    for (let i = 0; i < emailsToProcess.length; i++) {
      const email = emailsToProcess[i];

      // Skip emails that were pre-filtered in fetchRecentEmails
      if (email.skipped) {
        Logger.log(`Email ${i + 1}: Pre-filtered as spam/newsletter - skipping`);
        emailsSkippingGemini.push({
          email: email,
          analysis: {
            priority: 'LOW',
            summary: email.subject,
            todos: []
          }
        });
        continue;
      }

      // Quick pre-check: Skip Gemini for obvious low-priority emails
      const quickCheck = classifyWithRules(email);

      if (quickCheck.priority === 'LOW' && quickCheck.confidence > 0.8) {
        // Skip Gemini for obvious newsletters/marketing - save tokens!
        Logger.log(`Email ${i + 1}: Quick classification: ${quickCheck.priority} (skipping Gemini to save tokens)`);
        emailsSkippingGemini.push({
          email: email,
          analysis: {
            priority: 'LOW',
            summary: email.subject,
            todos: []
          }
        });
      } else {
        // This email needs Gemini analysis
        emailsNeedingGemini.push(email);
      }
    }

    // Process emails that skipped Gemini
    emailsSkippingGemini.forEach(({ email, analysis }) => {
      const result = {
        emailId: email.id,
        subject: email.subject,
        priority: analysis.priority,
        summary: analysis.summary,
        todos: analysis.todos
      };
      results.push(result);
      cacheResult(email.id, result);

      emailSummaries.push({
        subject: email.subject,
        sender: email.sender,
        priority: analysis.priority,
        summary: analysis.summary,
        timestamp: email.timestamp,
        id: email.id
      });
    });

    // Parallel Gemini API calls for emails that need it
    if (emailsNeedingGemini.length > 0) {
      Logger.log(`Making ${emailsNeedingGemini.length} parallel Gemini API calls...`);

      try {
        const geminiAnalyses = batchAnalyzeEmailsWithGemini(emailsNeedingGemini);

        // Process Gemini results
        for (let i = 0; i < emailsNeedingGemini.length; i++) {
          const email = emailsNeedingGemini[i];
          const analysis = geminiAnalyses[i];

          if (analysis.error) {
            Logger.log(`✗ Email ${i + 1} Gemini error: ${analysis.error}`);
            // Fallback to rule-based
            const quickCheck = classifyWithRules(email);
            analysis.priority = quickCheck.priority;
            analysis.summary = email.subject;
            analysis.todos = [];
          } else {
            Logger.log(`✓ Email ${i + 1} Gemini analysis: ${analysis.priority} priority, ${analysis.todos.length} to-dos`);
          }

          const result = {
            emailId: email.id,
            subject: email.subject,
            priority: analysis.priority,
            summary: analysis.summary,
            todos: analysis.todos
          };

          // Cache result
          cacheResult(email.id, result);
          results.push(result);

          // Add to email summaries
          emailSummaries.push({
            subject: email.subject,
            sender: email.sender,
            priority: analysis.priority,
            summary: analysis.summary,
            timestamp: email.timestamp,
            id: email.id
          });
        }

      } catch (batchError) {
        Logger.log(`Error in batch Gemini processing: ${batchError}`);
        // Fallback to rule-based for all
        emailsNeedingGemini.forEach(email => {
          const quickCheck = classifyWithRules(email);
          const result = {
            emailId: email.id,
            subject: email.subject,
            priority: quickCheck.priority,
            summary: email.subject,
            todos: []
          };
          cacheResult(email.id, result);
          results.push(result);

          emailSummaries.push({
            subject: email.subject,
            sender: email.sender,
            priority: quickCheck.priority,
            summary: email.subject,
            timestamp: email.timestamp,
            id: email.id
          });
        });
      }
    }

    Logger.log(`✓ Processed ${results.length} emails`);

    // Calculate progress
    const totalEmails = emails.length;
    const analyzedCount = emails.filter(e => getCachedResult(e.id)).length;
    const pendingEmails = totalEmails - analyzedCount;

    Logger.log(`Progress: ${analyzedCount} analyzed (${analyzedCount - newEmailsProcessed} cached + ${newEmailsProcessed} new), ${pendingEmails} pending`);

    // Collect all to-dos from results
    const allTodos = [];
    results.forEach(result => {
      if (result.todos && result.todos.length > 0) {
        result.todos.forEach(todo => {
          allTodos.push({
            task: todo,
            priority: result.priority,
            subject: result.subject,
            sender: result.sender,
            emailId: result.id
          });
        });
      }
    });

    Logger.log(`✓ Collected ${allTodos.length} to-dos from ${results.length} emails`);

    // Filter to only show emails with actionable to-dos OR that have important content
    // Don't filter LOW priority if they have to-dos
    const emailsWithTodos = emailSummaries.filter(email => {
      const todoCount = allTodos.filter(t => t.emailId === email.id).length;
      // Show if: has to-dos OR is HIGH/MEDIUM priority
      return todoCount > 0 || email.priority === 'HIGH' || email.priority === 'MEDIUM';
    });

    Logger.log(`✓ ${emailsWithTodos.length} emails displayed (${emailSummaries.length - emailsWithTodos.length} filtered out)`);

    // Sort email summaries by priority then by time
    sortBy = sortBy || 'priority';
    if (sortBy === 'priority') {
      emailsWithTodos.sort((a, b) => {
        const priorityOrder = { 'HIGH': 0, 'MEDIUM': 1, 'LOW': 2 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      });
    } else if (sortBy === 'time') {
      emailsWithTodos.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    }

    // Build email list card with progress info
    return buildEmailListCard(emailsWithTodos, sortBy, {
      total: totalEmails,
      analyzed: analyzedCount,
      pending: pendingEmails,
      allTodos: allTodos,
      totalProcessed: emailSummaries.length
    });

  } catch (error) {
    Logger.log('✗ Error in showEmailList: ' + error);
    Logger.log('Stack trace: ' + error.stack);
    return buildErrorCard('Failed to load email list: ' + error.toString());
  }
}

/**
 * Build simplified email list card with clickable links
 */
function buildEmailListCard(emailSummaries, currentSort, progress) {
  const card = CardService.newCardBuilder();

  let subtitle = `${emailSummaries.length} emails with tasks`;
  if (progress && progress.totalProcessed) {
    const skipped = progress.totalProcessed - emailSummaries.length;
    subtitle = `${emailSummaries.length} actionable | ${skipped} skipped`;
  }
  if (progress && progress.pending > 0) {
    subtitle += ` (${progress.pending} processing...)`;
  }

  card.setHeader(CardService.newCardHeader()
    .setTitle('Email Organizer')
    .setSubtitle(subtitle));

  // Sort options section
  const sortSection = CardService.newCardSection();

  const sortByPriorityAction = CardService.newAction()
    .setFunctionName('sortByPriority');

  const sortByTimeAction = CardService.newAction()
    .setFunctionName('sortByTime');

  const priorityButton = CardService.newTextButton()
    .setText(currentSort === 'priority' ? 'By Priority ✓' : 'By Priority')
    .setOnClickAction(sortByPriorityAction);

  const timeButton = CardService.newTextButton()
    .setText(currentSort === 'time' ? 'By Time ✓' : 'By Time')
    .setOnClickAction(sortByTimeAction);

  sortSection.addWidget(CardService.newDecoratedText()
    .setText('<b>Sort by:</b>')
    .setButton(priorityButton));

  sortSection.addWidget(CardService.newDecoratedText()
    .setText('')
    .setButton(timeButton));

  card.addSection(sortSection);

  // Email Summary section - clickable email items grouped by priority
  if (emailSummaries && emailSummaries.length > 0) {
    const highEmails = emailSummaries.filter(e => e.priority === 'HIGH');
    const medEmails = emailSummaries.filter(e => e.priority === 'MEDIUM');
    const lowEmails = emailSummaries.filter(e => e.priority === 'LOW');

    // HIGH priority emails
    if (highEmails.length > 0) {
      const highSection = CardService.newCardSection()
        .setHeader(`HIGH PRIORITY (${highEmails.length} emails)`);

      highEmails.forEach((email, idx) => {
        const emailLink = `https://mail.google.com/mail/u/0/#inbox/${email.id}`;
        const todoCount = progress.allTodos ? progress.allTodos.filter(t => t.emailId === email.id).length : 0;

        // Format summary title - capitalize first letter of each word after colon
        let displaySummary = email.summary || email.subject;
        if (displaySummary.includes(':')) {
          const parts = displaySummary.split(':');
          displaySummary = `${parts[0].trim()}: ${parts.slice(1).join(':').trim()}`;
        }

        const decoratedText = CardService.newDecoratedText()
          .setText(`<b>${displaySummary}</b>\n<font color="#666666">${email.subject}</font>\n<i>${todoCount} task${todoCount !== 1 ? 's' : ''}</i> • From: ${email.sender.split('<')[0].trim()}`)
          .setOpenLink(CardService.newOpenLink()
            .setUrl(emailLink)
            .setOpenAs(CardService.OpenAs.FULL_SIZE)
            .setOnClose(CardService.OnClose.NOTHING));

        highSection.addWidget(decoratedText);

        if (idx < highEmails.length - 1) {
          highSection.addWidget(CardService.newDivider());
        }
      });

      card.addSection(highSection);
    }

    // MEDIUM priority emails
    if (medEmails.length > 0) {
      const medSection = CardService.newCardSection()
        .setHeader(`MEDIUM PRIORITY (${medEmails.length} emails)`);

      medEmails.slice(0, 10).forEach((email, idx) => {
        const emailLink = `https://mail.google.com/mail/u/0/#inbox/${email.id}`;
        const todoCount = progress.allTodos ? progress.allTodos.filter(t => t.emailId === email.id).length : 0;

        // Format summary title
        let displaySummary = email.summary || email.subject;
        if (displaySummary.includes(':')) {
          const parts = displaySummary.split(':');
          displaySummary = `${parts[0].trim()}: ${parts.slice(1).join(':').trim()}`;
        }

        const decoratedText = CardService.newDecoratedText()
          .setText(`<b>${displaySummary}</b>\n<font color="#666666">${email.subject}</font>\n<i>${todoCount} task${todoCount !== 1 ? 's' : ''}</i> • From: ${email.sender.split('<')[0].trim()}`)
          .setOpenLink(CardService.newOpenLink()
            .setUrl(emailLink)
            .setOpenAs(CardService.OpenAs.FULL_SIZE)
            .setOnClose(CardService.OnClose.NOTHING));

        medSection.addWidget(decoratedText);

        if (idx < medEmails.length - 1) {
          medSection.addWidget(CardService.newDivider());
        }
      });

      if (medEmails.length > 10) {
        medSection.addWidget(CardService.newTextParagraph()
          .setText(`<i>...and ${medEmails.length - 10} more medium priority emails</i>`));
      }

      card.addSection(medSection);
    }

    // LOW priority emails
    if (lowEmails.length > 0) {
      const lowSection = CardService.newCardSection()
        .setHeader(`LOW PRIORITY (${lowEmails.length} emails)`);

      lowEmails.slice(0, 5).forEach((email, idx) => {
        const emailLink = `https://mail.google.com/mail/u/0/#inbox/${email.id}`;
        const todoCount = progress.allTodos ? progress.allTodos.filter(t => t.emailId === email.id).length : 0;

        // Format summary title
        let displaySummary = email.summary || email.subject;
        if (displaySummary.includes(':')) {
          const parts = displaySummary.split(':');
          displaySummary = `${parts[0].trim()}: ${parts.slice(1).join(':').trim()}`;
        }

        const decoratedText = CardService.newDecoratedText()
          .setText(`<b>${displaySummary}</b>\n<i>${todoCount} task${todoCount !== 1 ? 's' : ''}</i>`)
          .setOpenLink(CardService.newOpenLink()
            .setUrl(emailLink)
            .setOpenAs(CardService.OpenAs.FULL_SIZE)
            .setOnClose(CardService.OnClose.NOTHING));

        lowSection.addWidget(decoratedText);

        if (idx < lowEmails.length - 1) {
          lowSection.addWidget(CardService.newDivider());
        }
      });

      if (lowEmails.length > 5) {
        lowSection.addWidget(CardService.newTextParagraph()
          .setText(`<i>...and ${lowEmails.length - 5} more low priority emails</i>`));
      }

      card.addSection(lowSection);
    }
  } else {
    // No actionable emails found
    const emptySection = CardService.newCardSection();
    emptySection.addWidget(CardService.newTextParagraph()
      .setText('No actionable emails found.\n\nAll analyzed emails have no tasks or are low priority.'));
    card.addSection(emptySection);
  }

  // Footer with refresh button and progress info
  const footerSection = CardService.newCardSection();

  // Show progress info if processing is incomplete
  if (progress && progress.pending > 0) {
    footerSection.addWidget(CardService.newTextParagraph()
      .setText(`<b>Processing in batches...</b>\n${progress.analyzed}/${progress.total} emails analyzed\n\nClick to process ${Math.min(5, progress.pending)} more emails`));
  }

  // Refresh button
  const refreshAction = CardService.newAction()
    .setFunctionName('refreshTodoList');

  const refreshButton = CardService.newTextButton()
    .setText(progress && progress.pending > 0 ? 'Process More' : 'Refresh Analysis')
    .setOnClickAction(refreshAction);

  footerSection.addWidget(CardService.newDecoratedText()
    .setText('')
    .setButton(refreshButton));

  // Clear cache & refresh button
  const clearCacheAction = CardService.newAction()
    .setFunctionName('clearCacheAndRefresh');

  const clearCacheButton = CardService.newTextButton()
    .setText('Clear Cache & Refresh')
    .setOnClickAction(clearCacheAction);

  footerSection.addWidget(CardService.newDecoratedText()
    .setText('<font color="#999999">Force reload all emails (clears cache)</font>')
    .setButton(clearCacheButton));

  card.addSection(footerSection);

  return [card.build()];
}

/**
 * Sort email list by priority
 */
function sortByPriority(e) {
  return showEmailList(e, 'priority');
}

/**
 * Sort email list by time
 */
function sortByTime(e) {
  return showEmailList(e, 'time');
}

/**
 * Refresh email list (processes next batch without clearing cache)
 */
function refreshTodoList(e) {
  // Just reload - will process next batch of uncached emails
  return showEmailList(e, 'priority');
}

/**
 * Clear cache and force refresh all emails
 */
function clearCacheAndRefresh(e) {
  try {
    Logger.log('=== Clearing cache and refreshing ===');

    // Clear all cached results
    clearCache();
    Logger.log('✓ Cache cleared');

    // Reload email list - will re-analyze all emails
    return showEmailList(e, 'priority');

  } catch (error) {
    Logger.log('✗ Error clearing cache: ' + error);
    return buildErrorCard('Failed to clear cache: ' + error.toString());
  }
}

/**
 * Analyze all emails from the last 24 hours
 */
function analyzeDailyEmails(e) {
  try {
    Logger.log('=== Starting daily email analysis ===');

    // Fetch recent emails
    let emails = [];
    try {
      emails = fetchRecentEmails(24); // Last 24 hours
      Logger.log(`✓ Found ${emails.length} emails`);
    } catch (fetchError) {
      Logger.log('✗ Error fetching emails: ' + fetchError);
      Logger.log('Stack trace: ' + fetchError.stack);
      return buildErrorCard('Failed to fetch emails: ' + fetchError.toString() + '\n\nCheck View > Logs for details');
    }

    if (emails.length === 0) {
      return buildInfoCard('No emails found in the last 24 hours');
    }

    // Filter out already cached emails
    const uncachedEmails = emails.filter(email => {
      return !getCachedResult(email.id);
    });

    Logger.log(`${uncachedEmails.length} new emails to analyze, ${emails.length - uncachedEmails.length} from cache`);

    // Batch classify emails using API
    const results = [];
    let processedCount = 0;
    let errorCount = 0;

    for (let i = 0; i < emails.length; i++) {
      const email = emails[i];

      try {
        Logger.log(`\n--- Processing email ${i + 1}/${emails.length}: "${email.subject.substring(0, 50)}..." ---`);

        // Check cache first
        let cached = getCachedResult(email.id);
        if (cached) {
          Logger.log(`✓ Using cached result`);
          cached.cached = true;
          results.push(cached);
          processedCount++;
          continue;
        }

        // Classify with API
        let classification;
        try {
          classification = classifyWithAPI(email);
          Logger.log(`✓ API classification: ${classification.priority} (${Math.round(classification.confidence * 100)}%)`);
        } catch (classifyError) {
          Logger.log(`✗ API classification failed: ${classifyError}`);
          classification = { error: classifyError.toString() };
        }

        if (classification.error) {
          // Fallback to rules
          Logger.log('Using fallback rule-based classification');
          classification = classifyWithRules(email);
          Logger.log(`✓ Rule-based: ${classification.priority}`);
        }

        // Generate to-dos for all priorities
        let todos = [];
        try {
          todos = generateTodosWithGemini(email, classification.priority);
          Logger.log(`✓ Generated ${todos.length} to-dos`);
        } catch (geminiError) {
          Logger.log(`✗ Gemini to-do generation failed: ${geminiError}`);
          todos = [];
        }

        const result = {
          subject: email.subject,
          priority: classification.priority,
          confidence: classification.confidence,
          todos: todos.slice(0, 3), // Top 3 only
          cached: false,
          sender: email.sender,
          id: email.id
        };

        // Cache result
        try {
          cacheResult(email.id, result);
        } catch (cacheError) {
          Logger.log(`✗ Cache save failed: ${cacheError}`);
        }

        results.push(result);
        processedCount++;

      } catch (emailError) {
        errorCount++;
        Logger.log(`✗ Error processing email "${email.subject}": ${emailError}`);
        Logger.log('Stack trace: ' + emailError.stack);

        // Add partial result with error flag
        results.push({
          subject: email.subject,
          priority: 'MEDIUM',
          confidence: 0.5,
          todos: [],
          error: emailError.toString(),
          cached: false,
          sender: email.sender,
          id: email.id
        });
      }
    }

    Logger.log(`\n=== Analysis complete ===`);
    Logger.log(`Total: ${emails.length} emails`);
    Logger.log(`Processed: ${processedCount} emails`);
    Logger.log(`Errors: ${errorCount} emails`);

    // Build summary card
    return buildDailySummaryCard(results);

  } catch (error) {
    Logger.log('\n✗✗✗ CRITICAL ERROR in analyzeDailyEmails ✗✗✗');
    Logger.log('Error: ' + error.toString());
    Logger.log('Stack trace: ' + error.stack);
    Logger.log('Error name: ' + error.name);
    Logger.log('Error message: ' + error.message);

    return buildErrorCard(
      'Critical error during analysis:\n\n' +
      error.toString() +
      '\n\nCheck View > Logs for full details'
    );
  }
}

/**
 * Fetch recent emails from Gmail using built-in GmailApp
 */
function fetchRecentEmails(hours) {
  Logger.log(`\n--- fetchRecentEmails: Looking for emails from last ${hours} hours ---`);

  const oneDayAgo = new Date();
  oneDayAgo.setHours(oneDayAgo.getHours() - hours);

  // Calculate timestamp for Gmail search
  const year = oneDayAgo.getFullYear();
  const month = oneDayAgo.getMonth() + 1;
  const day = oneDayAgo.getDate();

  // Only search in Primary inbox (exclude Promotions, Social, Updates, Forums)
  const query = `in:inbox category:primary after:${year}/${month}/${day}`;
  Logger.log(`Gmail search query: "${query}"`);

  try {
    // Use GmailApp.search instead of Gmail API
    Logger.log('Executing GmailApp.search...');
    const threads = GmailApp.search(query, 0, 50); // Max 50 threads

    if (!threads || threads.length === 0) {
      Logger.log('No threads found');
      return [];
    }

    Logger.log(`Found ${threads.length} threads`);
    const emails = [];

    // Process each thread
    for (let i = 0; i < threads.length; i++) {
      try {
        Logger.log(`\nProcessing thread ${i + 1}/${threads.length}...`);
        const messages = threads[i].getMessages();
        Logger.log(`  Thread has ${messages.length} messages`);

        // Get the first message from each thread
        if (messages.length > 0) {
          const message = messages[0];

          try {
            const subject = message.getSubject() || '(No Subject)';
            Logger.log(`  Subject: "${subject.substring(0, 50)}..."`);

            const from = message.getFrom() || 'Unknown';
            Logger.log(`  From: ${from}`);

            const date = message.getDate().toISOString();

            // STRATEGY 1: Early Skip Detection - Check for obvious spam/newsletters BEFORE fetching body
            const sender = from.toLowerCase();
            const subjectLower = subject.toLowerCase();

            let shouldSkip = false;

            // Marketing sender patterns - exclude legitimate service emails
            const marketingSenderPatterns = [
              'newsletter@', 'news@', 'marketing@', 'promo@', 'promotions@', 'offers@'
            ];

            // Check sender patterns - be more conservative
            if (marketingSenderPatterns.some(pattern => sender.includes(pattern))) {
              shouldSkip = true;
              Logger.log(`  ⚡ SKIP: Marketing sender detected (${from})`);
            }

            // Check for legitimate action emails that shouldn't be skipped
            const actionKeywords = ['password', 'reset', 'verify', 'confirm', 'activate', 'security', 'alert'];
            const isActionEmail = actionKeywords.some(kw => subjectLower.includes(kw));

            // Marketing subject keywords - only skip if NOT an action email
            const marketingSubjectKeywords = [
              'newsletter', 'daily digest', 'weekly summary', 'monthly newsletter',
              'sale', 'discount', 'coupon', 'limited time', 'shop now', 'buy now',
              'special offer', 'exclusive offer', 'flash sale', 'today only'
            ];

            if (!isActionEmail && marketingSubjectKeywords.some(kw => subjectLower.includes(kw))) {
              shouldSkip = true;
              Logger.log(`  ⚡ SKIP: Marketing keyword in subject`);
            }

            // Check for emojis commonly used in marketing
            if (subjectLower.includes('✨') || subjectLower.includes('🎉') ||
                subjectLower.includes('🔥') || subjectLower.includes('💰') ||
                subjectLower.includes('🎁') || subjectLower.includes('%') ||
                subjectLower.includes('$')) {
              shouldSkip = true;
              Logger.log(`  ⚡ SKIP: Marketing emoji/symbol in subject`);
            }

            // If marked to skip, add minimal email object without fetching body
            if (shouldSkip) {
              const emailObj = {
                id: message.getId(),
                subject: subject,
                body: '',  // Don't fetch body for obvious spam
                sender: from,
                timestamp: date,
                skipped: true  // Mark as pre-filtered
              };
              emails.push(emailObj);
              Logger.log(`  ✓ Email added (pre-filtered, no body fetch)`);
              continue;  // Skip to next thread - HUGE time savings!
            }

            // STRATEGY 4: Reduce body fetch size from 2000 to 800 chars
            // Only fetch body for potentially actionable emails
            let plainBody = '';
            try {
              Logger.log('  Getting plain body...');
              plainBody = message.getPlainBody() || '';
              Logger.log(`  ✓ Body length: ${plainBody.length} chars`);
            } catch (bodyError) {
              Logger.log(`  ✗ Error getting body: ${bodyError}`);
              Logger.log(`  Body error stack: ${bodyError.stack}`);
              plainBody = '(Could not extract email body)';
            }

            // Clean body text - remove non-ASCII characters that cause encoding issues
            let cleanBody = '';
            try {
              // Keep only ASCII printable chars, newlines, and tabs
              cleanBody = plainBody.replace(/[^\x20-\x7E\n\r\t]/g, ' ');
              Logger.log(`  ✓ Cleaned body length: ${cleanBody.length} chars`);
            } catch (cleanError) {
              Logger.log(`  ✗ Error cleaning body: ${cleanError}`);
              cleanBody = 'Error processing email body';
            }

            const emailObj = {
              id: message.getId(),
              subject: subject,
              body: cleanBody.substring(0, 800),  // Reduced from 2000 to 800
              sender: from,
              timestamp: date
            };

            emails.push(emailObj);
            Logger.log(`  ✓ Email added to results`);

          } catch (msgError) {
            Logger.log(`  ✗ Error processing message: ${msgError}`);
            Logger.log(`  Message error stack: ${msgError.stack}`);
            // Skip this message and continue
          }
        }
      } catch (threadError) {
        Logger.log(`✗ Error processing thread ${i + 1}: ${threadError}`);
        Logger.log(`Thread error stack: ${threadError.stack}`);
        // Continue with next thread
      }
    }

    Logger.log(`\n✓ Successfully fetched ${emails.length} emails from ${threads.length} threads`);
    return emails;

  } catch (error) {
    Logger.log('\n✗✗✗ CRITICAL ERROR in fetchRecentEmails ✗✗✗');
    Logger.log(`Error: ${error}`);
    Logger.log(`Error name: ${error.name}`);
    Logger.log(`Error message: ${error.message}`);
    Logger.log(`Stack trace: ${error.stack}`);
    throw error;
  }
}

/**
 * Build summary card showing all analyzed emails
 */
function buildDailySummaryCard(results) {
  const card = CardService.newCardBuilder();

  card.setHeader(CardService.newCardHeader()
    .setTitle('📊 Daily Email Summary')
    .setSubtitle(`${results.length} emails analyzed`));

  // Group by priority
  const high = results.filter(r => r.priority === 'HIGH');
  const medium = results.filter(r => r.priority === 'MEDIUM');
  const low = results.filter(r => r.priority === 'LOW');

  // HIGH priority section
  if (high.length > 0) {
    const highSection = CardService.newCardSection()
      .setHeader(`🔴 HIGH PRIORITY (${high.length})`);

    high.forEach(email => {
      let text = `<b>${email.subject}</b>`;
      if (email.todos && email.todos.length > 0) {
        text += `\n${email.todos.slice(0, 3).map(t => `• ${t}`).join('\n')}`;
      }
      highSection.addWidget(CardService.newTextParagraph().setText(text));
      highSection.addWidget(CardService.newDivider());
    });

    card.addSection(highSection);
  }

  // MEDIUM priority section
  if (medium.length > 0) {
    const medSection = CardService.newCardSection()
      .setHeader(`🟡 MEDIUM PRIORITY (${medium.length})`);

    medium.slice(0, 5).forEach(email => { // Show max 5
      let text = `<b>${email.subject}</b>`;
      if (email.todos && email.todos.length > 0) {
        text += `\n${email.todos.slice(0, 2).map(t => `• ${t}`).join('\n')}`;
      }
      medSection.addWidget(CardService.newTextParagraph().setText(text));
    });

    if (medium.length > 5) {
      medSection.addWidget(CardService.newTextParagraph()
        .setText(`<i>...and ${medium.length - 5} more</i>`));
    }

    card.addSection(medSection);
  }

  // LOW priority section
  if (low.length > 0) {
    const lowSection = CardService.newCardSection()
      .setHeader(`🟢 LOW PRIORITY (${low.length})`);

    lowSection.addWidget(CardService.newTextParagraph()
      .setText(`<i>Low priority emails (skipped to save tokens)</i>`));

    card.addSection(lowSection);
  }

  // Footer with refresh button
  const footerSection = CardService.newCardSection();

  const refreshAction = CardService.newAction()
    .setFunctionName('analyzeDailyEmails');

  const refreshButton = CardService.newTextButton()
    .setText('🔄 Refresh Analysis')
    .setOnClickAction(refreshAction);

  footerSection.addWidget(refreshButton);
  card.addSection(footerSection);

  return [card.build()];
}

/**
 * Build info card for messages
 */
function buildInfoCard(message) {
  const card = CardService.newCardBuilder();

  card.setHeader(CardService.newCardHeader()
    .setTitle('ℹ️ Info'));

  const section = CardService.newCardSection();
  section.addWidget(CardService.newTextParagraph().setText(message));

  card.addSection(section);

  return [card.build()];
}

/**
 * Build card to display analysis results
 */
function buildResultCard(result) {
  const card = CardService.newCardBuilder();

  // Header
  card.setHeader(CardService.newCardHeader()
    .setTitle('Email Analysis')
    .setSubtitle(result.subject || 'No subject'));

  // Priority section
  const prioritySection = CardService.newCardSection();

  const priorityEmoji = {
    'HIGH': '🔴',
    'MEDIUM': '🟡',
    'LOW': '🟢'
  };

  const emoji = priorityEmoji[result.priority] || '⚪';
  const confidencePercent = Math.round((result.confidence || 0) * 100);

  prioritySection.addWidget(CardService.newKeyValue()
    .setTopLabel('Priority')
    .setContent(`${emoji} ${result.priority}`)
    .setBottomLabel(`${confidencePercent}% confidence`));

  if (result.cached) {
    prioritySection.addWidget(CardService.newTextParagraph()
      .setText('✅ <b>Loaded from cache</b>'));
  }

  card.addSection(prioritySection);

  // To-dos section
  if (result.todos && result.todos.length > 0) {
    const todoSection = CardService.newCardSection()
      .setHeader('📋 Action Items');

    const todoText = result.todos.map((todo, i) => `${i + 1}. ${todo}`).join('\n\n');

    todoSection.addWidget(CardService.newTextParagraph()
      .setText(todoText));

    card.addSection(todoSection);
  } else if (result.priority === 'LOW') {
    const infoSection = CardService.newCardSection();
    infoSection.addWidget(CardService.newTextParagraph()
      .setText('ℹ️ <i>LOW priority emails skipped to save tokens</i>'));
    card.addSection(infoSection);
  }

  // Reason section (if available)
  if (result.reason) {
    const reasonSection = CardService.newCardSection();
    reasonSection.addWidget(CardService.newTextParagraph()
      .setText(`<i>${result.reason}</i>`));
    card.addSection(reasonSection);
  }

  return [card.build()];
}

/**
 * Build error card
 */
function buildErrorCard(error) {
  const card = CardService.newCardBuilder();

  card.setHeader(CardService.newCardHeader()
    .setTitle('⚠️ Error')
    .setSubtitle('Could not analyze email'));

  const section = CardService.newCardSection();
  section.addWidget(CardService.newTextParagraph()
    .setText(`Error: ${error}\n\nPlease check:\n• API server is running\n• ngrok URL is correct\n• API_KEY matches .env`));

  card.addSection(section);

  return [card.build()];
}

/**
 * Process email using hybrid approach:
 * 1. ML Model API → Classify priority
 * 2. Check cache
 * 3. Gemini API → Generate to-dos (if not cached)
 */
function processEmailHybrid(email) {
  try {
    // Step 1: Check cache first
    const cached = getCachedResult(email.id);
    if (cached) {
      cached.cached = true;
      return cached;
    }

    // Step 2: Classify priority using ML model API
    const classification = classifyWithAPI(email);

    if (classification.error) {
      // Fallback to rule-based if API fails
      classification = classifyWithRules(email);
    }

    // Step 3: Generate to-dos with Gemini (all priorities)
    let todos = [];
    try {
      todos = generateTodosWithGemini(email, classification.priority);
    } catch (error) {
      Logger.log('Error generating todos: ' + error);
      todos = [];
    }

    const result = {
      subject: email.subject,
      priority: classification.priority,
      confidence: classification.confidence,
      reason: classification.reason || '',
      todos: todos,
      cached: false
    };

    // Cache the result
    cacheResult(email.id, result);

    return result;

  } catch (error) {
    Logger.log('Error processing email: ' + error);
    return {
      error: error.toString(),
      priority: 'MEDIUM',
      confidence: 0.5,
      todos: []
    };
  }
}

/**
 * Classify email using ML model API
 */
function classifyWithAPI(email) {
  const url = `${API_URL}/api/classify`;

  const payload = {
    email: {
      subject: email.subject,
      body: email.body
    }
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const result = JSON.parse(response.getContentText());

    if (result.error) {
      throw new Error(result.error);
    }

    return {
      priority: result.priority,
      confidence: result.confidence,
      reason: 'ML model classification'
    };

  } catch (error) {
    Logger.log('API classification error: ' + error);
    return {
      error: error.toString()
    };
  }
}

/**
 * Fallback: Rule-based classification (enhanced for better pre-filtering)
 */
function classifyWithRules(email) {
  const text = (email.subject + ' ' + email.body.substring(0, 500)).toLowerCase();
  const sender = email.sender.toLowerCase();
  const subject = email.subject.toLowerCase();

  // High priority keywords
  const highKeywords = ['urgent', 'asap', 'critical', 'emergency', 'important', 'deadline', 'immediately', 'action required'];

  // Check for legitimate action emails first
  const actionKeywords = ['password', 'reset', 'verify', 'confirm', 'activate', 'security', 'alert', 'expire', 'expiring'];
  const isActionEmail = actionKeywords.some(kw => text.includes(kw));

  // Marketing/newsletter detection - less aggressive
  const marketingKeywords = [
    'newsletter', 'unsubscribe', 'marketing email', 'promotional email',
    'daily digest', 'weekly summary', 'monthly newsletter',
    'sale', 'discount', 'coupon', 'limited time offer',
    'shop now', 'buy now', 'special offer', 'exclusive offer',
    'flash sale', 'today only', 'don\'t miss out'
  ];

  // Marketing sender patterns - more conservative
  const marketingSenders = [
    'newsletter@', 'news@', 'marketing@', 'promo@', 'promotions@', 'offers@'
  ];

  let highScore = 0;
  let marketingScore = 0;
  let confidence = 0.7;

  // Check for high priority keywords
  highKeywords.forEach(kw => { if (text.includes(kw)) highScore++; });

  // Don't count marketing keywords for action emails
  if (!isActionEmail) {
    marketingKeywords.forEach(kw => { if (text.includes(kw)) marketingScore++; });
  }

  // Check sender patterns - only specific marketing domains
  let isMarketingSender = false;
  marketingSenders.forEach(pattern => {
    if (sender.includes(pattern)) {
      isMarketingSender = true;
      marketingScore += 2;
      confidence = 0.85;
    }
  });

  // Check for common marketing subject patterns
  if (subject.includes('✨') || subject.includes('🎉') || subject.includes('🔥') ||
      subject.includes('💰') || subject.includes('🎁') || subject.includes('%') ||
      subject.includes('$') || subject.match(/\d+%\s*(off|discount)/)) {
    marketingScore += 2;
    confidence = 0.85;
  }

  // Check for unsubscribe links (very strong indicator of marketing)
  if (text.includes('unsubscribe') || text.includes('opt out') ||
      text.includes('opt-out') || text.includes('manage preferences') ||
      text.includes('update your preferences')) {
    marketingScore += 3;
    confidence = 0.95;
  }

  // Determine priority
  let priority = 'MEDIUM';

  // Action emails should be MEDIUM or HIGH, never LOW
  if (isActionEmail) {
    priority = highScore > 0 ? 'HIGH' : 'MEDIUM';
    confidence = 0.8;
  } else if (marketingScore >= 2) {
    // Need at least 2 marketing indicators to mark as LOW
    priority = 'LOW';
    confidence = Math.min(0.85 + (marketingScore * 0.02), 0.95);
  } else if (highScore > 0) {
    priority = 'HIGH';
    confidence = 0.8;
  }

  return {
    priority: priority,
    confidence: confidence,
    reason: 'Rule-based classification'
  };
}

/**
 * Analyze email with Gemini: priority + to-dos + summary in one call
 */
function analyzeEmailWithGemini(email) {
  // Smart body truncation - keep first 600 chars (usually contains key info)
  const bodyPreview = email.body.substring(0, 600);

  const prompt = `Analyze email. Return JSON only.

Subject: ${email.subject}
From: ${email.sender}
Body: ${bodyPreview}

Priority: HIGH (urgent/deadline), MEDIUM (action needed), LOW (newsletter/FYI)
Summary: action-focused title using format "Action: Object" (e.g., "Review: Budget Report", "Complete: Training Module", "Respond: Client Inquiry")
Todos: specific actionable tasks with deadlines if mentioned

JSON format:
{"priority":"HIGH|MEDIUM|LOW","summary":"Action: Object","todos":["task1","task2"]}

Response:`;

  try {
    const response = callGeminiAPI(prompt);

    // Parse JSON
    let text = response.trim();

    // Remove markdown code blocks if present
    if (text.includes('```')) {
      text = text.split('```')[1];
      if (text.startsWith('json')) {
        text = text.substring(4);
      }
      text = text.split('```')[0];
    }

    const analysis = JSON.parse(text.trim());

    // Validate response structure
    if (!analysis.priority || !analysis.summary) {
      throw new Error('Invalid Gemini response structure');
    }

    // Ensure todos is an array
    if (!Array.isArray(analysis.todos)) {
      analysis.todos = [];
    }

    return analysis;

  } catch (error) {
    Logger.log('Gemini analysis error: ' + error);
    Logger.log('Response was: ' + response);
    throw error;
  }
}

/**
 * Call Gemini API
 */
function callGeminiAPI(prompt) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`;

  const payload = {
    contents: [{
      parts: [{
        text: prompt
      }]
    }]
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const responseText = response.getContentText();
    const result = JSON.parse(responseText);

    if (result.error) {
      Logger.log(`Gemini API error: ${JSON.stringify(result.error)}`);
      throw new Error(`Gemini API error: ${result.error.message || result.error}`);
    }

    if (result.candidates && result.candidates.length > 0) {
      return result.candidates[0].content.parts[0].text;
    } else {
      Logger.log(`Unexpected Gemini response: ${responseText}`);
      throw new Error('No response from Gemini');
    }
  } catch (error) {
    Logger.log(`✗ Gemini API call failed: ${error}`);
    throw error;
  }
}

/**
 * Get email details from Gmail
 */
function getEmailDetails(messageId, accessToken) {
  const url = `https://gmail.googleapis.com/gmail/v1/users/me/messages/${messageId}`;

  const response = UrlFetchApp.fetch(url, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
    muteHttpExceptions: true
  });

  const message = JSON.parse(response.getContentText());

  // Check if message has valid structure
  if (!message || !message.payload) {
    throw new Error('Invalid email message structure');
  }

  const headers = message.payload.headers || [];
  const subject = getHeader(headers, 'Subject') || '(No Subject)';
  const from = getHeader(headers, 'From') || 'Unknown sender';
  const date = getHeader(headers, 'Date') || new Date().toISOString();
  const body = getEmailBody(message.payload);

  return {
    id: messageId,
    subject: subject,
    body: body && body.length > 0 ? body.substring(0, 2000) : 'No content',
    sender: from,
    timestamp: date
  };
}

function getHeader(headers, name) {
  // Safety check for headers array
  if (!headers || !Array.isArray(headers)) {
    return null;
  }

  for (let i = 0; i < headers.length; i++) {
    if (headers[i] && headers[i].name && headers[i].name.toLowerCase() === name.toLowerCase()) {
      return headers[i].value;
    }
  }
  return null;
}

function getEmailBody(payload) {
  let body = '';

  if (payload.parts) {
    for (let i = 0; i < payload.parts.length; i++) {
      const part = payload.parts[i];
      if (part.mimeType === 'text/plain' && part.body.data) {
        body = Utilities.newBlob(Utilities.base64Decode(part.body.data)).getDataAsString();
        break;
      }
    }
  } else if (payload.body && payload.body.data) {
    body = Utilities.newBlob(Utilities.base64Decode(payload.body.data)).getDataAsString();
  }

  return body;
}

/**
 * Cache management
 */
function getCachedResult(emailId) {
  const cache = PropertiesService.getUserProperties();
  const key = 'email_' + emailId;
  const cached = cache.getProperty(key);

  if (cached) {
    return JSON.parse(cached);
  }
  return null;
}

function cacheResult(emailId, result) {
  const cache = PropertiesService.getUserProperties();
  const key = 'email_' + emailId;

  // Don't cache error results
  if (!result.error) {
    cache.setProperty(key, JSON.stringify(result));
  }
}

/**
 * STRATEGY 3: Batch cache lookups - get multiple cached results at once
 * Much faster than calling getCachedResult() in a loop
 */
function batchGetCachedResults(emailIds) {
  const cache = PropertiesService.getUserProperties();
  const results = {};

  // PropertiesService.getProperties() is faster than multiple getProperty() calls
  const allProps = cache.getProperties();

  emailIds.forEach(emailId => {
    const key = 'email_' + emailId;
    if (allProps[key]) {
      try {
        results[emailId] = JSON.parse(allProps[key]);
      } catch (e) {
        Logger.log(`Error parsing cached result for ${emailId}: ${e}`);
        results[emailId] = null;
      }
    } else {
      results[emailId] = null;
    }
  });

  return results;
}

/**
 * STRATEGY 2: Batch analyze emails with Gemini using parallel API calls
 * Uses UrlFetchApp.fetchAll() to make multiple API calls in parallel
 * This is MUCH faster than sequential calls (2s each → 2s total for all)
 */
function batchAnalyzeEmailsWithGemini(emails) {
  if (emails.length === 0) {
    return [];
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`;

  // Build array of request objects for fetchAll
  const requests = emails.map(email => {
    const bodyPreview = email.body.substring(0, 600);

    const prompt = `Analyze email. Return JSON only.

Subject: ${email.subject}
From: ${email.sender}
Body: ${bodyPreview}

Priority: HIGH (urgent/deadline), MEDIUM (action needed), LOW (newsletter/FYI)
Summary: action-focused title using format "Action: Object" (e.g., "Review: Budget Report", "Complete: Training Module", "Respond: Client Inquiry")
Todos: specific actionable tasks with deadlines if mentioned

JSON format:
{"priority":"HIGH|MEDIUM|LOW","summary":"Action: Object","todos":["task1","task2"]}

Response:`;

    const payload = {
      contents: [{
        parts: [{
          text: prompt
        }]
      }]
    };

    return {
      url: url,
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
  });

  Logger.log(`⚡ Making ${requests.length} parallel Gemini API calls...`);

  try {
    // fetchAll makes all requests in parallel - HUGE speedup!
    const responses = UrlFetchApp.fetchAll(requests);

    // Parse all responses
    const analyses = responses.map((response, idx) => {
      try {
        const responseText = response.getContentText();
        const result = JSON.parse(responseText);

        if (result.error) {
          Logger.log(`Email ${idx + 1} Gemini API error: ${JSON.stringify(result.error)}`);
          return { error: `Gemini API error: ${result.error.message || result.error}` };
        }

        if (result.candidates && result.candidates.length > 0) {
          let text = result.candidates[0].content.parts[0].text.trim();

          // Remove markdown code blocks if present
          if (text.includes('```')) {
            text = text.split('```')[1];
            if (text.startsWith('json')) {
              text = text.substring(4);
            }
            text = text.split('```')[0];
          }

          const analysis = JSON.parse(text.trim());

          // Validate response structure
          if (!analysis.priority || !analysis.summary) {
            return { error: 'Invalid Gemini response structure' };
          }

          // Ensure todos is an array
          if (!Array.isArray(analysis.todos)) {
            analysis.todos = [];
          }

          return analysis;
        } else {
          Logger.log(`Email ${idx + 1} unexpected Gemini response: ${responseText}`);
          return { error: 'No response from Gemini' };
        }
      } catch (error) {
        Logger.log(`Email ${idx + 1} parse error: ${error}`);
        return { error: error.toString() };
      }
    });

    Logger.log(`✓ Completed ${analyses.length} parallel Gemini API calls`);
    return analyses;

  } catch (error) {
    Logger.log(`✗ Batch Gemini API call failed: ${error}`);
    // Return error for all emails
    return emails.map(() => ({ error: error.toString() }));
  }
}

function getCacheStats() {
  const cache = PropertiesService.getUserProperties();
  const keys = cache.getKeys();
  const emailKeys = keys.filter(k => k.startsWith('email_'));

  return {
    count: emailKeys.length
  };
}

function clearCache() {
  const cache = PropertiesService.getUserProperties();
  cache.deleteAllProperties();
  return { message: 'Cache cleared' };
}
