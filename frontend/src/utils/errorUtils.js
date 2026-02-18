export const isNetworkError = (error) => {
  return error.name === 'TypeError' && 
         error.message.toLowerCase().includes('failed to fetch');
};

