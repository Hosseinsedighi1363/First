import React, { useContext } from 'react';
import { Drawer, List, ListItem, ListItemText, ListItemButton, IconButton, Box, useTheme } from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';
import { ColorModeContext } from '../App';

const Layout = ({ children }) => {
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);

  return (
    <div style={{ display: 'flex' }}>
      <Drawer
        variant="permanent"
        anchor="right"
      >
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 1 }}>
          <IconButton
            onClick={colorMode.toggleColorMode}
            color="inherit"
            aria-label="toggle theme"
          >
            {theme.palette.mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
          </IconButton>
        </Box>
        <List>
          {['داشبورد', 'پروفایل', 'تکالیف', 'آزمون‌ها'].map((text) => (
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