import React from 'react';
import { Grid, Card, CardContent, Typography, CardHeader, Box } from '@mui/material';

const Dashboard = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        داشبورد دانشجو
      </Typography>
      <Typography paragraph>
        به داشبورد خود خوش آمدید. در اینجا می‌توانید تکالیف، آزمون‌ها و پروفایل خود را مشاهده کنید.
      </Typography>
      <Grid container spacing={3}>
        {/* Upcoming Assignments Card */}
        <Grid xs={12} md={6}>
          <Card>
            <CardHeader title="تکالیف پیش‌رو" />
            <CardContent>
              <Typography>تکلیف ریاضی - فصل ۳ (مهلت: ۳ روز دیگر)</Typography>
              <Typography>پروژه فیزیک - ارائه نهایی (مهلت: ۱ هفته دیگر)</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Grades Card */}
        <Grid xs={12} md={6}>
          <Card>
            <CardHeader title="آخرین نمرات ثبت‌شده" />
            <CardContent>
              <Typography>آزمون شیمی: ۱۹.۵</Typography>
              <Typography>کوییز ادبیات: ۲۰</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Calendar Card */}
        <Grid xs={12}>
          <Card>
            <CardHeader title="تقویم آموزشی" />
            <CardContent>
              <Typography>
                [در اینجا یک کامپوننت تقویم برای نمایش تاریخ آزمون‌ها و ددلاین‌ها قرار خواهد گرفت]
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;