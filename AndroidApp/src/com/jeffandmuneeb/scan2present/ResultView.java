package com.jeffandmuneeb.scan2present;

import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.Environment;
import android.util.AttributeSet;
import android.view.View;

public class ResultView extends View {
	private static final String TAG = "ResultView";
	private final static String DOWNLOAD_IMG_FILENAME = "/download.jpg";

	public Bitmap resultImage;
	public String filename;
	public Paint paintBlack;

	Rect src, dst;
	
	public ResultView(Context context, AttributeSet attrs) {
		super(context);
		
		filename = Environment.getExternalStorageDirectory().toString() + DOWNLOAD_IMG_FILENAME;

		BitmapFactory.Options options = new BitmapFactory.Options();
		options.inSampleSize = 1;

		resultImage = BitmapFactory.decodeFile(filename, options);

		paintBlack = new Paint();
		paintBlack.setStyle(Paint.Style.FILL);
		paintBlack.setColor(Color.BLACK);

		src = new Rect(0, 0, 300, 300);
		dst = new Rect(0, 0, 300, 300);
	}
	
	// Draws an image bitmap on the view
	protected void onDraw(Canvas canvas){
		canvas.drawColor(Color.RED);

		if (resultImage != null && !isInEditMode()) {
			// Draw the bitmap
			src.set(0, 0, resultImage.getWidth(), resultImage.getHeight());
			dst.set(0, 0, canvas.getWidth(), canvas.getHeight());

			canvas.drawBitmap(resultImage, null, dst, paintBlack);
		}
	}
}
