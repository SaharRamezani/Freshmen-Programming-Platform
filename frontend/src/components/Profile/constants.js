/**
 * Constants for Profile component
 */

export const ERROR_MESSAGES = {
  LOAD_FAILED: 'Failed to load profile.',
  UPDATE_FAILED: 'Failed to update profile.',
};

export const SUCCESS_MESSAGES = {
  UPDATED: 'Profile updated successfully',
};

export const BADGE_ICON_MAP = {
  // TopN badges
  'Champion': '/badges/TopN/1.png',
  'Podium Master': '/badges/TopN/3.png',
  'Elite Performer': '/badges/TopN/5.png',
  'Rising Star': '/badges/TopN/10.png',

  // FindingCodeFailures badges
  'Bug Hunter': '/badges/FindingCodeFailures/5.png',
  'Bug Tracker': '/badges/FindingCodeFailures/10.png',
  'Bug Slayer': '/badges/FindingCodeFailures/20.png',
  'Bug Exterminator': '/badges/FindingCodeFailures/50.png',
  'Bug Whisperer': '/badges/FindingCodeFailures/100.png',

  // CorrectUpVotes badges
  'Sharp Eye': '/badges/CorrectUpVotes/5.png',
  'Quality Checker': '/badges/CorrectUpVotes/10.png',
  'Insightful Reviewer': '/badges/CorrectUpVotes/20.png',
  'Truth Seeker': '/badges/CorrectUpVotes/50.png',
  'Peer Review Master': '/badges/CorrectUpVotes/100.png',

  // PassTeacherTests badges
  'First Pass': '/badges/PassTeacherTests/1.png',
  'Consistent Performer': '/badges/PassTeacherTests/5.png',
  'Reliable Solver': '/badges/PassTeacherTests/10.png',
  'Test Master': '/badges/PassTeacherTests/15.png',
  'Teachers Champion': '/badges/PassTeacherTests/20.png',

  // Finish Perfect badges
  'Flawless Start': '/badges/FinishPerfectly/1.png',
  'Clean Run': '/badges/FinishPerfectly/5.png',
  'Precision Player': '/badges/FinishPerfectly/10.png',
  'Perfectionist': '/badges/FinishPerfectly/15.png',
  'Untouchable': '/badges/FinishPerfectly/20.png',
};

export const DEFAULT_BADGE_ICON = '/badges/default_badge.png';

export const getBadgeIcon = (badge) => {
  return BADGE_ICON_MAP[badge.name] || DEFAULT_BADGE_ICON;
};
