import React from 'react';
import { Drawer, List, ListItem, ListItemText, ListItemButton } from '@mui/material';

const Layout = ({ children }) => {
  return (
    <div style={{ display: 'flex' }}>
      <Drawer
        variant="permanent"
        anchor="right"
      >
        <List>
          {['Dashboard', 'Profile', 'Assignments', 'Quizzes'].map((text) => (
            <ListItem key={text} disablePadding>
              <ListItemButton>
                <ListItemText primary={text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
      <main style={{ flexGrow: 1, padding: '24px' }}>
        {children}
      </main>
    </div>
  );
};

export default Layout;